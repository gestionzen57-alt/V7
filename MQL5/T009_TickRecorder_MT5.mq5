//+------------------------------------------------------------------+
//| PowerFlow T010 / B9 MT5 Raw Tick Recorder                         |
//| Writes raw MT5 ticks to CSV for Python import into tick_archive.db |
//| No trading. No Telegram. No powerflow.db writes.                  |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "PowerFlow B9 raw tick recorder for MT5"

input string InpSymbol = "";
input string InpOutputFileName = "";
input bool   InpUseCommonFiles = true;
input bool   InpEnableOnTickRaw = true;
input bool   InpEnableTimerSample = false;
input int    InpTimerSeconds = 1;
input bool   InpEnableHistoricalBackfill = false;
input int    InpHistoryMinutes = 60;
input bool   InpWriteHeaderIfEmpty = true;
input int    InpFlushEveryRows = 1;

string g_symbol;
string g_file_name;
long   g_capture_seq = 0;
long   g_last_time_msc = 0;
int    g_rows_since_flush = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   g_symbol = (InpSymbol == "" ? _Symbol : InpSymbol);
   if(!SymbolSelect(g_symbol, true))
   {
      Print("PowerFlow T009 recorder: SymbolSelect failed for ", g_symbol);
      return INIT_FAILED;
   }

   g_file_name = InpOutputFileName;
   if(g_file_name == "")
      g_file_name = "PowerFlow_T009_ticks_" + g_symbol + ".csv";

   EnsureHeader();

   if(InpEnableTimerSample)
      EventSetTimer(MathMax(1, InpTimerSeconds));

   if(InpEnableHistoricalBackfill)
      ExportHistoricalTicks(InpHistoryMinutes);

   Print("PowerFlow T009 MT5 TickRecorder initialized for ", g_symbol,
         " file=", g_file_name,
         " common=", (InpUseCommonFiles ? "true" : "false"));
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(InpEnableTimerSample)
      EventKillTimer();
   Print("PowerFlow T009 MT5 TickRecorder stopped for ", g_symbol, " reason=", reason);
}

//+------------------------------------------------------------------+
void OnTick()
{
   if(!InpEnableOnTickRaw)
      return;

   MqlTick tick;
   if(SymbolInfoTick(g_symbol, tick))
      WriteTick(tick, "ONTICK_RAW");
}

//+------------------------------------------------------------------+
void OnTimer()
{
   if(!InpEnableTimerSample)
      return;

   MqlTick tick;
   if(SymbolInfoTick(g_symbol, tick))
      WriteTick(tick, "TIMER_1S_SAMPLE");
}

//+------------------------------------------------------------------+
void ExportHistoricalTicks(int minutes)
{
   MqlTick ticks[];
   ulong to_msc = (ulong)TimeCurrent() * 1000;
   ulong from_msc = (ulong)(TimeCurrent() - minutes * 60) * 1000;

   int copied = CopyTicksRange(g_symbol, ticks, COPY_TICKS_ALL, from_msc, to_msc);
   if(copied <= 0)
   {
      Print("PowerFlow T009 historical CopyTicksRange returned ", copied,
            " for ", g_symbol, " error=", GetLastError());
      return;
   }

   for(int i = 0; i < copied; i++)
      WriteTick(ticks[i], "HISTORICAL_RAW");

   Print("PowerFlow T009 historical ticks exported: ", copied, " for ", g_symbol);
}

//+------------------------------------------------------------------+
void EnsureHeader()
{
   if(!InpWriteHeaderIfEmpty)
      return;

   int flags = FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI;
   if(InpUseCommonFiles)
      flags |= FILE_COMMON;

   int handle = FileOpen(g_file_name, flags, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("PowerFlow T009 recorder cannot open file for header: ", g_file_name,
            " error=", GetLastError());
      return;
   }

   if(FileSize(handle) == 0)
   {
      FileWrite(handle,
         "symbol", "time", "time_msc", "bid", "ask", "last", "mid", "spread",
         "volume", "volume_real", "flags", "source_mode", "broker", "server_time",
         "capture_seq", "gap_ms", "quality_flags"
      );
   }
   FileClose(handle);
}

//+------------------------------------------------------------------+
void WriteTick(const MqlTick &tick, string source_mode)
{
   double bid = tick.bid;
   double ask = tick.ask;
   double last = tick.last;
   double mid = 0.0;
   double spread = 0.0;

   if(bid > 0.0 && ask > 0.0)
   {
      mid = (bid + ask) / 2.0;
      spread = ask - bid;
   }
   else if(last > 0.0)
   {
      mid = last;
   }

   long gap_ms = 0;
   if(g_last_time_msc > 0 && tick.time_msc >= g_last_time_msc)
      gap_ms = tick.time_msc - g_last_time_msc;
   g_last_time_msc = tick.time_msc;

   g_capture_seq++;

   int flags = FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI;
   if(InpUseCommonFiles)
      flags |= FILE_COMMON;

   int handle = FileOpen(g_file_name, flags, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("PowerFlow T009 recorder FileOpen failed: ", g_file_name,
            " error=", GetLastError());
      return;
   }

   FileSeek(handle, 0, SEEK_END);

   string tick_time = TimeToString((datetime)tick.time, TIME_DATE | TIME_SECONDS);
   string server_time = TimeToString(TimeTradeServer(), TIME_DATE | TIME_SECONDS);
   string broker = AccountInfoString(ACCOUNT_COMPANY);
   string quality = BuildQualityFlags(bid, ask, spread, mid);

   FileWrite(handle,
      g_symbol,
      tick_time,
      (long)tick.time_msc,
      DoubleToString(bid, _Digits),
      DoubleToString(ask, _Digits),
      DoubleToString(last, _Digits),
      DoubleToString(mid, _Digits),
      DoubleToString(spread, _Digits),
      (long)tick.volume,
      DoubleToString(tick.volume_real, 2),
      (long)tick.flags,
      source_mode,
      broker,
      server_time,
      g_capture_seq,
      gap_ms,
      quality
   );

   g_rows_since_flush++;
   if(InpFlushEveryRows <= 1 || g_rows_since_flush >= InpFlushEveryRows)
   {
      FileFlush(handle);
      g_rows_since_flush = 0;
   }

   FileClose(handle);
}

//+------------------------------------------------------------------+
string BuildQualityFlags(double bid, double ask, double spread, double mid)
{
   string q = "";
   if(bid <= 0.0 || ask <= 0.0)
      q = AppendFlag(q, "BID_ASK_MISSING");
   if(spread < 0.0)
      q = AppendFlag(q, "SPREAD_NEGATIVE");
   if(mid <= 0.0)
      q = AppendFlag(q, "MID_MISSING");
   if(q == "")
      q = "OK";
   return q;
}

//+------------------------------------------------------------------+
string AppendFlag(string existing, string flag)
{
   if(existing == "")
      return flag;
   return existing + "|" + flag;
}
//+------------------------------------------------------------------+
