"""Snowflake I/O for the generator: read CLD keys, write ACOCO_SIM tables (write_pandas), hash tables."""
import os

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

CONNECTION = os.environ.get("ACOCO_CONNECTION", "sfseapac_kp")
SIM_DB = "ACOCO_SIM"


class Sf:
    def __init__(self):
        self.con = snowflake.connector.connect(connection_name=CONNECTION,
                                               server_session_keep_alive=False)
        self.cur = self.con.cursor()
        self.cur.execute("USE ROLE ACCOUNTADMIN")
        self.cur.execute("USE WAREHOUSE WH_ACOCO_BUILD")

    def close(self):
        self.con.close()

    def df(self, sql: str) -> pd.DataFrame:
        self.cur.execute(sql)
        return self.cur.fetch_pandas_all()

    def exec(self, sql: str):
        self.cur.execute(sql)

    def write(self, schema: str, table: str, frame: pd.DataFrame, quote: bool = False):
        """Replace ACOCO_SIM.<schema>.<table> with frame. quote=True keeps camelCase (BDC-shaped) column names."""
        self.exec(f"CREATE SCHEMA IF NOT EXISTS {SIM_DB}.{schema}")
        ok, _, nrows, _ = write_pandas(self.con, frame, table_name=table, database=SIM_DB, schema=schema,
                                       auto_create_table=True, overwrite=True, quote_identifiers=quote,
                                       use_logical_type=True, chunk_size=500_000)
        if not ok or nrows != len(frame):
            raise RuntimeError(f"load failed {schema}.{table}: {nrows}/{len(frame)}")
        return nrows
