from rd_territorial_system.ingestion import discover_one_main_table, load_one_table

if __name__ == "__main__":
    path = discover_one_main_table()
    _, report = load_one_table(path)
    print(report)
