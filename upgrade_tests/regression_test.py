"""
Home for upgrade-related tests that don't fit in with the core upgrade testing in dtest.upgrade_through_versions
"""
from cassandra import ConsistencyLevel as CL
from upgrade_base import UpgradeTester


class TestForRegressions(UpgradeTester):
    """
    Catch-all class for regression tests on specific versions.
    """
    NODES, RF, __test__, CL = 2, 1, True, CL.ONE

    def test_10822(self):
        """
        @jira_ticket CASSANDRA-10822
        """
        session = self.prepare()

        session.execute("CREATE KEYSPACE financial WITH replication={'class':'SimpleStrategy', 'replication_factor': 1};")
        session.execute("""
        create table if not exists financial.symbol_history (
          symbol text,
          name text,
          year int,
          month int,
          day int,
          volume bigint,
          close double,
          open double,
          low double,
          high double,
          primary key((symbol, year), month, day)
        ) with CLUSTERING ORDER BY (month desc, day desc);
        """)

        symbol_years = [('CORP', 2004), ('BLAH', 2005), ('FOO', 2006), ('BAR', 2007), ('HUH', 2008)]

        for symbol, year in symbol_years:
            for month in range(0, 50):
                session.execute("INSERT INTO financial.symbol_history (symbol, name, year, month, day, volume) VALUES ('{}', 'MegaCorp', {}, {}, 1, 100)".format(symbol, year, month))

        for symbol, year in symbol_years:
            session.execute("DELETE FROM financial.symbol_history WHERE symbol='{}' and year = {} and month=25;".format(symbol, year, month))

        sessions = self.do_upgrade(session)

        for s in sessions:
            expected_rows = 49

            for symbol, year in symbol_years:
                count = s[1].execute("select count(*) from financial.symbol_history where symbol='{}' and year={};".format(symbol, year))[0][0]
                self.assertEqual(count, expected_rows, "actual {} did not match expected {}".format(count, expected_rows))
