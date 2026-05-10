PowerFlow Memory V1.1 — Weekend pathfix + self-test

Remplacement direct :
  Core/pf_memory_engine.py
  Core/run_memory_query_once.py

Pourquoi :
  - Le Forex est ferme le week-end, donc la queue live peut etre vide.
  - Si le runner n'affiche pas le bloc "memory_engine", l'ancien fichier est encore execute.
  - Ce patch ajoute un diagnostic visible et un mode --self-test.

Installation novice :
  1) Extraire ce ZIP a la racine du projet GPT, pas dans Core.
     Exemple racine : C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
  2) Accepter le remplacement des fichiers.
  3) Ouvrir PowerShell dans ...\GPT\Core

Tests :
  python -m py_compile pf_memory_engine.py run_memory_query_once.py
  python run_memory_query_once.py --pretty

Validation week-end sans marche ouvert :
  python run_memory_query_once.py --self-test --pretty

Validation JSON PowerShell :
  python -m json.tool ..\output\memory_query_results.json | Out-Null

Si la queue live est ailleurs :
  Get-ChildItem ..\.. -Recurse -Filter behavioral_alert_queue.json | Select-Object FullName,Length,LastWriteTime
  python run_memory_query_once.py --queue "CHEMIN_COMPLET\behavioral_alert_queue.json" --pretty

Commit :
  git add Core/pf_memory_engine.py Core/run_memory_query_once.py
  git commit -m "Memory: V1 pattern indexing engine"
