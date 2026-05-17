//+------------------------------------------------------------------+
//| PowerFlow T010 / B9 MT5 Raw Tick Recorder                        |
//| Writes raw MT5 ticks to CSV for Python import into tick_archive.db|
//| No trading. No Telegram. No powerflow.db writes.                 |
//+------------------------------------------------------------------+
#property strict
#property version   "1.10"
#property description "PowerFlow B9 raw tick recorder for MT5"

input string InpSymbol = "";
input string InpOutputFileName = "";
input bool   InpUseCommonFiles = true;

input bool   InpEnableOnTickRaw = true;
input bool   InpEnableTimerSample = false;
input int    InpTimerSeconds = 1;

input bool   InpEnableHistoricalBackfill = false;
input int    InpHistoryMinutes = 60;

// T010.1: precise historical export. Priority over InpHistoryMinutes when enabled.
input bool   InpEnableHistoricalDateRange = false;
input string InpHistoricalStart = ""; // Example: 2026.05.15 08:00
input string InpHistoricalEnd = "";   // Example: 2026.05.15 12:00

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

   if(InpEnableHistoricalDateRange)
      ExportHistoricalTicksByDateRange(InpHistoricalStart, InpHistoricalEnd);
   else if(InpEnableHistoricalBackfill)
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
   datetime now = TimeCurrent();
   datetime from_dt = now - minutes * 60;
   ExportHistoricalTicksRange(from_dt, now, "HistoryMinutes");
}

//+------------------------------------------------------------------+
void ExportHistoricalTicksByDateRange(string start_text, string end_text)
{
   datetime from_dt = 0;
   datetime to_dt = 0;

   if(!ParseDateTimeInput(start_text, from_dt))
   {
      Print("PowerFlow T009 date-range export invalid InpHistoricalStart=", start_text,
            " expected format like 2026.05.15 08:00");
      return;
   }

   if(!ParseDateTimeInput(end_text, to_dt))
   {
      Print("PowerFlow T009 date-range export invalid InpHistoricalEnd=", end_text,
            " expected format like 2026.05.15 12:00");
      return;
   }

   if(to_dt <= from_dt)
   {
      Print("PowerFlow T009 date-range export rejected: end <= start. start=",
            TimeToString(from_dt, TIME_DATE | TIME_SECONDS),
            " end=", TimeToString(to_dt, TIME_DATE | TIME_SECONDS));
      return;
   }

   ExportHistoricalTicksRange(from_dt, to_dt, "DateRange");
}

//+------------------------------------------------------------------+
bool ParseDateTimeInput(string text, datetime &out_dt)
{
   string trimmed = text;
   StringTrimLeft(trimmed);
   StringTrimRight(trimmed);

   if(trimmed == "")
      return false;

   out_dt = StringToTime(trimmed);
   if(out_dt <= 0)
      return false;

   return true;
}

//+------------------------------------------------------------------+
void ExportHistoricalTicksRange(datetime from_dt, datetime to_dt, string label)
{
   MqlTick ticks[];
   ulong from_msc = (ulong)from_dt * 1000;
   ulong to_msc = (ulong)to_dt * 1000;

   Print("PowerFlow T009 historical export ", label,
         " symbol=", g_symbol,
         " from=", TimeToString(from_dt, TIME_DATE | TIME_SECONDS),
         " to=", TimeToString(to_dt, TIME_DATE | TIME_SECONDS),
         " from_msc=", from_msc,
         " to_msc=", to_msc);

   int copied = CopyTicksRange(g_symbol, ticks, COPY_TICKS_ALL, from_msc, to_msc);

   if(copied <= 0)
   {
      Print("PowerFlow T009 historical CopyTicksRange returned ", copied,
            " for ", g_symbol,
            " error=", GetLastError(),
            " from=", TimeToString(from_dt, TIME_DATE | TIME_SECONDS),
            " to=", TimeToString(to_dt, TIME_DATE | TIME_SECONDS));
      return;
   }

   for(int i = 0; i < copied; i++)
      WriteTick(ticks[i], "HISTORICAL_RAW");

   Print("PowerFlow T009 historical ticks exported: ", copied,
         " for ", g_symbol,
         " range=", TimeToString(from_dt, TIME_DATE | TIME_SECONDS),
         " -> ", TimeToString(to_dt, TIME_DATE | TIME_SECONDS));
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
                "capture_seq", "gap_ms", "quality_flags");
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
             quality);

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
