-- Rebuild steps run by tools/rollback.sh after databases are restored from checkpoint clones.
-- Grows with each checkpoint. CP-00 creates no Snowflake objects, so there is nothing to rebuild yet.
--
-- Planned content (added by the checkpoint that introduces each object):
--   CP-04+  ALTER DYNAMIC TABLE ... RESUME for every DT in ACOCO_L2 (cloned DTs start SUSPENDED - measured CP-00)
--   CP-06+  re-create Cortex Search services from sql/03_l2/reasoning/ (clones do not carry them - measured CP-00)
--   CP-08+  re-create agent ACOCO_DB.AGENT.ACOCO_ADVISOR from sql/04_agent/
--   CP-10+  ALTER SERVICE ACOCO_DB.APP.ACOCO_COMMAND_CENTER FROM SPECIFICATION (tagged image)
SELECT 'nothing to rebuild at CP-00' AS status;
