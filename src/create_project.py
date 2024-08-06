from pathlib import Path
import pandas as pd
from rich import print

class CreateProject:
    def create(self, path_file: Path):
        if not path_file.exists():
            print(f"File not found: {path_file}")
            return
        
        try:
            # Lees de "Cable list" sheet uit het Excel-bestand, en gebruik de eerste rij als kolomnamen
            df = pd.read_excel(path_file, sheet_name='Cable list ', header=1)
            return df
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def print_connections(self, df):
        if df is None or df.empty:
            print("No data to display.")
            return

        for index, row in df.iterrows():
            from_mark = row['from Mark']
            from_terminal = row['From terminal']
            to_mark = row['to mark']
            to_terminal = row['to terminal']

            print(f"{index + 1} : {from_mark} ({from_terminal}) -> {to_mark} ({to_terminal})")

if __name__ == "__main__":
    # Geef het juiste pad naar het geüploade bestand
    path_file = Path(__file__).parent.parent / "electrical_schemes/Cable & cabinet assembly list S25.xlsx"
    print(path_file)
    create = CreateProject()
    df_cable_list = create.create(path_file)
    create.print_connections(df_cable_list)
