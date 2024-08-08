import json
import os
from pathlib import Path
import pandas as pd
from rich import print

class CreateProject:
    important_marks = ["10CON1", "21C1", "21C2", "19C1", "17C1", "16C1", "8C1", "20C1", "20C2"]
    json_output_path = Path(__file__).parent.parent / "test_results/connections.json"
    testing_components_output_path = Path(__file__).parent.parent / "test_results/testing_components_answers.json"
    testing_components_results = Path(__file__).parent.parent / "test_results/test_results.json"

    def create(self, path_file: Path):
        path_file = Path(__file__).parent.parent / f"electrical_schemes/{path_file}"
        if not path_file.exists():
            print(f"File not found: {path_file}")
            return

        try:
            # Controleer alle werkbladnamen
            excel_file = pd.ExcelFile(path_file)
            sheet_name = None
            
            # Controleer op de mogelijke namen
            if 'Cable list' in excel_file.sheet_names:
                sheet_name = 'Cable list'
            elif 'Cable list ' in excel_file.sheet_names:
                sheet_name = 'Cable list '
            else:
                print("No valid sheet name found")
                return None

            # Lees het juiste werkblad en gebruik de eerste rij als kolomnamen
            df = pd.read_excel(path_file, sheet_name=sheet_name, header=None)
            cabinet_name = self.get_cabinet_name(df)
            df = pd.read_excel(path_file, sheet_name=sheet_name, header=1)
            
            organized_connections = self.organize_connections(df)
            self.save_connections_to_json(organized_connections, self.json_output_path)
            self.save_connections_to_json(self.filter_important_connections(organized_connections, self.important_marks), self.testing_components_output_path)
            
            # Maak het lege test_results.json bestand met de schakelkast naam
            self.create_empty_test_results(self.testing_components_results, cabinet_name)

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_cabinet_name(self, df):
        # Zoek de schakelkastnaam in de eerste rij
        return df.iloc[0, 1] if not pd.isna(df.iloc[0, 1]) else "Unknown Cabinet"

    def organize_connections(self, df):
        if df is None or df.empty:
            print("No data to display.")
            return
        
        organized_connections = {}
        
        for index, row in df.iterrows():
            from_mark = row['from Mark']
            to_mark = row['to mark']
            connection_from = {
                "from_terminal": row['From terminal'],
                "to_part": row['to part'],
                "to_mark": to_mark,
                "to_terminal": row['to terminal']
            }

            connection_to = {
                "from_terminal": row['to terminal'],
                "to_part": row['From Part'],
                "to_mark": from_mark,
                "to_terminal": row['From terminal']
            }
            
            if from_mark not in organized_connections:
                organized_connections[from_mark] = []
            
            organized_connections[from_mark].append(connection_from)

            # Voeg de verbinding ook toe aan de to_mark als een from_mark
            if to_mark not in organized_connections:
                organized_connections[to_mark] = []
            
            organized_connections[to_mark].append(connection_to)
        
        return organized_connections

    def filter_important_connections(self, connections, important_marks):
        filtered_connections = {mark: connections[mark] for mark in important_marks if mark in connections}
        return filtered_connections

    def save_connections_to_json(self, connections, json_path):
        try:
            # Verwijder het bestaande JSON-bestand als het bestaat
            if os.path.exists(json_path):
                os.remove(json_path)
            
            with open(json_path, 'w') as json_file:
                json.dump(connections, json_file, indent=4)
            print(f"Connections saved to {json_path}")
        except Exception as e:
            print(f"Failed to save connections to JSON: {e}")

    def create_empty_test_results(self, json_path, cabinet_name):
        # Maak een dictionary met de schakelkastnaam en lege arrays voor elke belangrijke markering
        empty_results = {
            "cabinet_name": cabinet_name,
            "test_results": {mark: [] for mark in self.important_marks}
        }

        try:
            # Verwijder het bestaande JSON-bestand als het bestaat
            if os.path.exists(json_path):
                os.remove(json_path)

            # Schrijf de lege testresultaten naar het JSON-bestand
            with open(json_path, 'w') as json_file:
                json.dump(empty_results, json_file, indent=4)
            print(f"Empty test results file created at {json_path}")
        except Exception as e:
            print(f"Failed to create empty test results JSON: {e}")

if __name__ == "__main__":
    # Geef het juiste pad naar het geüploade bestand
    path_file = "Cable & cabinet assembly list S25.xlsx"
    create = CreateProject()
    create.create(path_file)
