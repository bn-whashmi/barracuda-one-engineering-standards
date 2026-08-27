# Review Rerun Policy

After each fix:

1. Rerun the most local verification first.
2. Rerun any reviewer whose surface was directly changed.
3. Rerun adjacent security, contract, configuration, persistence, or migration
   checks when those surfaces changed.
4. Reconcile findings and workflow status before moving to the next fix.

Do not mark a blocking finding resolved based only on a code edit. Record the
verification evidence.
