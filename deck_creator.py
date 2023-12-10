import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
import genanki
import csv
import os
import pickle

# Chemins des fichiers de sauvegarde
DECK_SAVE_FILE = 'anki_deck_save.pkl'
SETTINGS_FILE = 'app_settings.pkl'

# Modèle personnalisé pour les cartes Anki
my_model = genanki.Model(
  1607392319,
  'Simple Model',
  fields=[
    {'name': 'Question'},
    {'name': 'Answer'}
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{Question}}',
      'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    },
  ])

class CustomDialog(tk.Toplevel):
    def __init__(self, parent, title=None, question=None, answer=None):
        super().__init__(parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        self.question = question or ""
        self.answer = answer or ""
        self.create_widgets()
        self.grab_set()
        if not question:
            self.question_entry.focus_set()
        else:
            self.answer_entry.focus_set()

    def create_widgets(self):
        self.question_label = tk.Label(self, text="Question:")
        self.question_label.grid(row=0, column=0)
        self.question_entry = tk.Entry(self)
        self.question_entry.grid(row=0, column=1)
        self.question_entry.insert(0, self.question)

        self.answer_label = tk.Label(self, text="Answer:")
        self.answer_label.grid(row=1, column=0)
        self.answer_entry = tk.Entry(self)
        self.answer_entry.grid(row=1, column=1)
        self.answer_entry.insert(0, self.answer)

        self.save_button = tk.Button(self, text="Save", command=self.on_save)
        self.save_button.grid(row=2, column=1)
        self.bind("<Return>", lambda event: self.on_save())

    def on_save(self):
        self.result = (self.question_entry.get(), self.answer_entry.get())
        self.parent.focus_set()
        self.destroy()

class AnkiDeckApp:
    def __init__(self, root):
        self.root = root
        self.settings = self.load_settings()
        root.title("Anki Deck Creator")
        self.deck = self.load_deck()
        self.create_widgets()
        self.apply_theme()
        self.populate_treeview()
        root.title("Anki Deck Creator")
        root.iconbitmap('C:\Root\Syncronisation\Import\Personnel\CODE\Python3\GenAnki\Genanki\Test_GUI\logo.ico')

    def create_widgets(self):
        self.tree = ttk.Treeview(self.root, columns=('Question', 'Answer'), show='headings', selectmode='extended')
        self.tree.heading('Question', text='Question')
        self.tree.heading('Answer', text='Answer')
        self.tree.pack(expand=True, fill='both')

        # Cadre pour les actions liées aux cartes
        cards_frame = tk.Frame(self.root)
        cards_frame.pack(pady=10)

        self.add_card_button = tk.Button(cards_frame, text="Add Card", command=self.add_card)
        self.add_card_button.grid(row=0, column=0, padx=5)

        self.edit_card_button = tk.Button(cards_frame, text="Edit Selected Card", command=self.edit_card)
        self.edit_card_button.grid(row=0, column=1, padx=5)

        self.delete_card_button = tk.Button(cards_frame, text="Delete Selected Cards", command=self.delete_cards)
        self.delete_card_button.grid(row=0, column=2, padx=5)

        # Cadre pour les actions d'import/export
        import_export_frame = tk.Frame(self.root)
        import_export_frame.pack(pady=10)

        self.import_csv_button = tk.Button(import_export_frame, text="Import Cards from CSV", command=self.import_from_csv)
        self.import_csv_button.grid(row=0, column=0, padx=5)

        self.export_deck_button = tk.Button(import_export_frame, text="Export Deck", command=self.export_deck)
        self.export_deck_button.grid(row=0, column=1, padx=5)

        # Bouton de bascule du thème
        self.toggle_theme_button = tk.Button(self.root, text="Toggle Dark Mode", command=self.toggle_theme)
        self.toggle_theme_button.pack(pady=10)
        
        # Status bar at the bottom of the window
        self.status_text = tk.StringVar()
        self.status_label = tk.Label(self.root, textvariable=self.status_text, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def add_card(self):
        dialog = CustomDialog(self.root, "Add Card")
        self.root.wait_window(dialog)
        question, answer = dialog.result
        if question and answer:
            card = genanki.Note(model=my_model, fields=[question, answer])
            self.deck.add_note(card)
            self.populate_treeview()
            self.save_deck()
            self.status_text.set("Card added.")

    def edit_card(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            old_question, old_answer = item['values']
            new_question = simpledialog.askstring("Edit Question", "Enter the new question:", initialvalue=old_question)
            new_answer = simpledialog.askstring("Edit Answer", "Enter the new answer:", initialvalue=old_answer)
            if new_question and new_answer:
                # Find and update the note in the deck
                for note in self.deck.notes:
                    if note.fields == [old_question, old_answer]:
                        note.fields = [new_question, new_answer]
                        break
                self.populate_treeview()
                self.save_deck()
                messagebox.showinfo("Success", "Card updated.")
        else:
            messagebox.showinfo("No Selection", "Please select a card to edit.")

    def delete_cards(self):
        selected_items = self.tree.selection()
        if selected_items:
            for item in selected_items:
                item_data = self.tree.item(item)
                question, answer = item_data['values']
                # Find and remove the note from the deck
                self.deck.notes = [note for note in self.deck.notes if note.fields != [question, answer]]
            self.populate_treeview()
            self.save_deck()
            messagebox.showinfo("Success", "Selected cards deleted.")
        else:
            messagebox.showinfo("No Selection", "Please select cards to delete.")

    def import_from_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                for row in reader:
                    if len(row) >= 2:
                        card = genanki.Note(model=my_model, fields=[row[0], row[1]])
                        self.deck.add_note(card)
            self.populate_treeview()
            self.save_deck()
            messagebox.showinfo("Success", "Cards imported from CSV.")

    def export_deck(self):
        try:
            genanki.Package(self.deck).write_to_file('custom_deck.apkg')
            messagebox.showinfo("Success", "Deck exported as 'custom_deck.apkg'.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def save_deck(self):
        with open(DECK_SAVE_FILE, 'wb') as f:
            pickle.dump(self.deck, f)

    def load_deck(self):
        if os.path.exists(DECK_SAVE_FILE):
            with open(DECK_SAVE_FILE, 'rb') as f:
                return pickle.load(f)
        return genanki.Deck(2059400110, "Custom Deck")

    def toggle_theme(self):
        self.settings['dark_mode'] = not self.settings.get('dark_mode', False)
        self.save_settings()
        self.apply_theme()

    def apply_theme(self):
        style = ttk.Style(self.root)
        if self.settings.get('dark_mode', False):
            self.root.configure(bg='black')
            style.configure("Treeview", background="black", fieldbackground="black", foreground="white")
            style.configure("Treeview.Heading", foreground="white", background="black")
        else:
            self.root.configure(bg='white')
            style.configure("Treeview", background="white", fieldbackground="white", foreground="black")
            style.configure("Treeview.Heading", foreground="black", background="white")


    def save_settings(self):
        with open(SETTINGS_FILE, 'wb') as f:
            pickle.dump(self.settings, f)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'rb') as f:
                return pickle.load(f)
        return {}

    def populate_treeview(self):
        # Clear the existing items in the treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
        # Add new items from the deck
        for note in self.deck.notes:
            self.tree.insert('', 'end', values=(note.fields[0], note.fields[1]))

def main():
    root = tk.Tk()
    app = AnkiDeckApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
