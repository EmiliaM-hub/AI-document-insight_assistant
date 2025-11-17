import gradio as gr
import os
import sys

# Dodaj ścieżkę do modułów src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import analyze_document
from src.config import check_config, REPO_DOCS_DIR
from pathlib import Path

def list_repo_documents():
    """Zwraca listę dokumentów z folderu testowego."""
    docs = []
    if REPO_DOCS_DIR.exists() and REPO_DOCS_DIR.is_dir():
        docs.extend([str(p) for p in REPO_DOCS_DIR.glob("*.pdf")])
        docs.extend([str(p) for p in REPO_DOCS_DIR.glob("*.docx")])
    return sorted([Path(d).name for d in docs])

def process_document(source_type, uploaded_file, url_input, repo_doc_dropdown):
    """
    Przetwarza dokument z wybranego źródła.
    
    Args:
        source_type: "upload", "url", lub "repo"
        uploaded_file: Plik przesłany przez użytkownika
        url_input: URL podany przez użytkownika
        repo_doc_dropdown: Dokument wybrany z folderu testowego
    """
    try:
        # Określ źródło dokumentu
        if source_type == "Upload lokalnego pliku z dysku" and uploaded_file:
            file_path = uploaded_file.name
            source_label = f"Plik lokalny: {Path(file_path).name}"
            
        elif source_type == "URL (np. GitHub)" and url_input:
            file_path = url_input.strip()
            source_label = f"URL: {url_input[:50]}..."
            
        elif source_type == "Folder testowy (data/test_docs/)" and repo_doc_dropdown:
            file_path = str(REPO_DOCS_DIR / repo_doc_dropdown)
            source_label = f"Folder testowy: {repo_doc_dropdown}"
            
        else:
            return "Nie wybrano żadnego dokumentu", "", "Błąd: wybierz źródło i dokument"
        
        # Analizuj dokument
        print(f"\n{'='*60}")
        print(f"[DEBUG] Rozpoczynam analizę: {file_path}")
        print(f"{'='*60}")
        
        result = analyze_document(file_path)
        
        print(f"\n[DEBUG] Klucze w result: {list(result.keys())}")
        
        summary = result.get("summary", "Brak streszczenia")
        key_points = result.get("key_points", [])
        
        if not summary or summary == "Brak streszczenia":
            print("[WARNING] Streszczenie jest puste!")
        
        if not key_points:
            print("[WARNING] Brak kluczowych punktów!")
        
        # Formatuj wyniki
        if key_points:
            key_points_text = "\n".join([f"• {point}" for point in key_points])
        else:
            key_points_text = "Brak kluczowych punktów"
        
        status = (
            f"Przeanalizowano!\n"
            f"Źródło: {source_label}\n"
            f"Stron: {result.get('page_count', 'N/A')}\n"
            f"Znaki oryginału: {len(result.get('text', ''))}\n"
            f"Znaki streszczenia: {len(summary)}"
        )
        
        print(f"\n[DEBUG] Zwracam:")
        print(f"  - Summary length: {len(summary)}")
        print(f"  - Key points count: {len(key_points)}")
        print(f"{'='*60}\n")
        
        return summary, key_points_text, status
        
    except Exception as e:
        print(f"\n[ERROR] Wyjątek: {e}")
        import traceback
        traceback.print_exc()
        return f"Błąd: {str(e)}", "", "Błąd przetwarzania"

# Sprawdź konfigurację przed uruchomieniem
print("Sprawdzanie konfiguracji...")
check_config()

# Pobierz listę dokumentów z folderu testowego
repo_docs = list_repo_documents()

# Interfejs Gradio
with gr.Blocks(title="AI Document Insight Assistant", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("""
    # AI Document Insight Assistant
    
     Automatyczna analiza dokumentów PDF i DOCX z wykorzystaniem Azure AI.
        
    **Obsługiwane źródła dokumentów:**
    - Upload lokalnego pliku z dysku
    - URL do pliku (np. GitHub, Google Drive)
    - Dokumenty z folderu testowego projektu
    """)

    with gr.Row():
        with gr.Column():
            # Wybór źródła dokumentu
            source_type = gr.Radio(
                choices=[
                    "Upload lokalnego pliku z dysku",
                    "URL (np. GitHub)",
                    "Folder testowy (data/test_docs/)"
                ],
                label="Wybierz źródło dokumentu",
                value="Upload lokalnego pliku z dysku"
            )
            
            # Upload pliku
            file_input = gr.File(
                label="Prześlij dokument (PDF/DOCX)",
                file_types=[".pdf", ".docx"],
                type="filepath",
                visible=True
            )
            
            # URL input
            url_input = gr.Textbox(
                label="Podaj URL do pliku",
                placeholder="https://example.com/dokument.pdf",
                visible=False
            )
            
            # Dropdown z dokumentami testowymi
            repo_dropdown = gr.Dropdown(
                choices=repo_docs,
                label="Wybierz dokument z folderu testowego",
                visible=False
            )
            
            # Przycisk analizy
            analyze_btn = gr.Button("Analizuj dokument", variant="primary", size="lg")
            
            # Status
            status_output = gr.Textbox(
                label="Status",
                lines=5,
                interactive=False
            )
        
        with gr.Column():
            # Streszczenie
            summary_output = gr.Textbox(
                label="Streszczenie",
                lines=10,
                interactive=False
            )
            
            # Kluczowe punkty
            key_points_output = gr.Textbox(
                label="Kluczowe punkty",
                lines=10,
                interactive=False
            )
    
    # Instrukcje (opcjonalne, zwijane)
    with gr.Accordion("Instrukcja i informacje techniczne", open=False):
        gr.Markdown("""
        ### Jak korzystać?
    1. Wybierz źródło dokumentu (upload, URL lub folder testowy)
    2. Podaj/wybierz dokument
    3. Kliknij "Analizuj dokument"
    4. Poczekaj na wyniki (10-20 sekund)
    
    ### Technologie:
    - **Azure AI Document Intelligence** - ekstrakcja tekstu z dokumentów
    - **Azure OpenAI (GPT-4o)** - generowanie streszczeń i analizy
    - **Gradio** - interfejs webowy
        """)
    
   # Funkcja do pokazywania/ukrywania inputów w zależności od wyboru
    def update_visibility(choice):
        return (
            gr.update(visible=(choice == "Upload lokalnego pliku z dysku")),
            gr.update(visible=(choice == "URL (np. GitHub)")),
            gr.update(visible=(choice == "Folder testowy (data/test_docs/)"))
        )
    
    # Połącz zmianę source_type z widocznością inputów
    source_type.change(
        fn=update_visibility,
        inputs=source_type,
        outputs=[file_input, url_input, repo_dropdown]
    )
    
    # Połącz przycisk z funkcją
    analyze_btn.click(
        fn=process_document,
        inputs=[source_type, file_input, url_input, repo_dropdown],
        outputs=[summary_output, key_points_output, status_output]
    )

# Uruchom aplikację
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)