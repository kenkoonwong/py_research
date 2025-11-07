import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os


class ResponseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Response Classifier")
        self.root.geometry("600x550")

        # Data storage
        self.df = None
        self.responses_df = pd.DataFrame(columns=['id', 'response'])
        self.current_id = None
        self.processed_ids = set()
        self.results_file = "result.csv"
        self.current_data_folder = None

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="Data Response Classifier",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Load data button
        load_btn = tk.Button(self.root, text="Load CSV File",
                            command=self.load_data,
                            font=("Arial", 12),
                            bg="#4CAF50", fg="white", padx=20, pady=5)
        load_btn.pack(pady=10)

        # Display frame
        self.display_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        self.display_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        # ID label
        self.id_label = tk.Label(self.display_frame, text="ID: ",
                                 font=("Arial", 14, "bold"))
        self.id_label.pack(pady=10)

        # Data display (scrollable)
        self.data_text = tk.Text(self.display_frame, height=10, width=60,
                                font=("Arial", 11), state=tk.DISABLED)
        self.data_text.pack(pady=10, padx=10)

        # Buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        # Positive button
        self.positive_btn = tk.Button(btn_frame, text="Positive",
                                     command=lambda: self.record_response("positive"),
                                     font=("Arial", 12), bg="#2196F3",
                                     fg="white", padx=30, pady=10,
                                     state=tk.DISABLED)
        self.positive_btn.pack(side=tk.LEFT, padx=10)

        # Negative button
        self.negative_btn = tk.Button(btn_frame, text="Negative",
                                     command=lambda: self.record_response("negative"),
                                     font=("Arial", 12), bg="#f44336",
                                     fg="white", padx=30, pady=10,
                                     state=tk.DISABLED)
        self.negative_btn.pack(side=tk.LEFT, padx=10)

        # Progress label
        self.progress_label = tk.Label(self.root, text="", font=("Arial", 10))
        self.progress_label.pack(pady=5)

        # Export button
        self.export_btn = tk.Button(self.root, text="Export Responses",
                                   command=self.export_responses,
                                   font=("Arial", 10), state=tk.DISABLED)
        self.export_btn.pack(pady=5)

    def load_existing_results(self, folder_path):
        """Load existing result.csv if it exists in the same folder"""
        result_path = os.path.join(folder_path, self.results_file)

        if os.path.exists(result_path):
            try:
                existing_results = pd.read_csv(result_path)
                if 'id' in existing_results.columns and 'response' in existing_results.columns:
                    self.responses_df = existing_results
                    self.processed_ids = set(existing_results['id'].tolist())
                    return True
            except Exception as e:
                print(f"Warning: Could not load existing results: {e}")

        return False

    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path)

            # Validate columns
            required_cols = ['id', 'name', 'value']
            if not all(col in self.df.columns for col in required_cols):
                messagebox.showerror("Error",
                    f"CSV must contain columns: {', '.join(required_cols)}")
                return

            # Store the folder path
            self.current_data_folder = os.path.dirname(file_path)

            # Load existing results from result.csv if present
            existing_found = self.load_existing_results(self.current_data_folder)

            if existing_found:
                num_existing = len(self.processed_ids)
                messagebox.showinfo("Info",
                    f"Loaded {len(self.df)} records\n"
                    f"Found existing result.csv with {num_existing} responses\n"
                    f"Filtering out already processed IDs...")
            else:
                # Reset responses if no existing file
                self.responses_df = pd.DataFrame(columns=['id', 'response'])
                self.processed_ids = set()

            # Load first ID
            if not self.load_next_id():
                return

            # Enable buttons
            self.positive_btn.config(state=tk.NORMAL)
            self.negative_btn.config(state=tk.NORMAL)
            self.export_btn.config(state=tk.NORMAL)

            if not existing_found:
                messagebox.showinfo("Success", f"Loaded {len(self.df)} records")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def load_next_id(self):
        # Get unique IDs that haven't been processed
        unique_ids = self.df['id'].unique()
        unprocessed_ids = [uid for uid in unique_ids if uid not in self.processed_ids]

        if not unprocessed_ids:
            messagebox.showinfo("Complete",
                "All IDs have been processed!\n\n"
                "Don't forget to export your responses.")
            self.positive_btn.config(state=tk.DISABLED)
            self.negative_btn.config(state=tk.DISABLED)
            return False

        # Load next ID
        self.current_id = unprocessed_ids[0]
        self.display_current_id()
        return True

    def display_current_id(self):
        # Get data for current ID
        id_data = self.df[self.df['id'] == self.current_id]

        # Update ID label
        self.id_label.config(text=f"ID: {self.current_id}")

        # Update data display
        self.data_text.config(state=tk.NORMAL)
        self.data_text.delete(1.0, tk.END)

        # Display name and value for this ID
        for idx, row in id_data.iterrows():
            self.data_text.insert(tk.END, f"Name: {row['name']}\n")
            self.data_text.insert(tk.END, f"Value: {row['value']}\n")
            self.data_text.insert(tk.END, "-" * 50 + "\n")

        self.data_text.config(state=tk.DISABLED)

        # Update progress
        total_ids = self.df['id'].nunique()
        processed = len(self.processed_ids)
        self.progress_label.config(
            text=f"Progress: {processed}/{total_ids} IDs processed"
        )

    def save_to_result_file(self):
        """Automatically append to result.csv in the data folder"""
        if self.current_data_folder is None:
            return

        result_path = os.path.join(self.current_data_folder, self.results_file)

        try:
            self.responses_df.to_csv(result_path, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to result.csv: {str(e)}")

    def record_response(self, response):
        if self.current_id is None:
            return

        # Add response to dataframe
        new_response = pd.DataFrame({
            'id': [self.current_id],
            'response': [response]
        })
        self.responses_df = pd.concat([self.responses_df, new_response],
                                     ignore_index=True)

        # Mark as processed
        self.processed_ids.add(self.current_id)

        # Automatically save to result.csv
        self.save_to_result_file()

        # Load next ID
        self.load_next_id()

    def export_responses(self):
        if self.responses_df.empty:
            messagebox.showwarning("Warning", "No responses to export!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Responses",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                self.responses_df.to_csv(file_path, index=False)
                messagebox.showinfo("Success",
                    f"Responses exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error",
                    f"Failed to export: {str(e)}")


def main():
    root = tk.Tk()
    app = ResponseGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
