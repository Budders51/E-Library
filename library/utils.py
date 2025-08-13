import fitz  # PyMuPDF
import os
from django.conf import settings
import uuid
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import nltk
from collections import Counter

# Download NLTK data jika belum ada
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def convert_pdf_to_images(pdf_path, book_id):
    """
    Konversi PDF ke gambar menggunakan PyMuPDF
    Returns: folder path yang berisi gambar-gambar hasil konversi
    """
    try:
        print(f"Debug: Starting PDF conversion for {pdf_path}")

        # Buat folder untuk menyimpan gambar
        images_folder = f"book_images/{book_id}_{uuid.uuid4().hex[:8]}"
        images_dir = os.path.join(settings.MEDIA_ROOT, images_folder)
        os.makedirs(images_dir, exist_ok=True)

        # Buka PDF
        pdf_document = fitz.open(pdf_path)

        for page_num in range(len(pdf_document)):
            # Ambil halaman
            page = pdf_document.load_page(page_num)

            # Konversi ke gambar dengan resolusi tinggi
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom untuk kualitas lebih baik
            pix = page.get_pixmap(matrix=mat)

            # Simpan sebagai PNG
            image_path = os.path.join(images_dir, f"page_{page_num + 1:03d}.png")
            pix.save(image_path)
            print(f"Debug: Saved page {page_num + 1} to {image_path}")

        pdf_document.close()
        print(f"Debug: PDF conversion completed. Images folder: {images_folder}")

        # Return relative path untuk disimpan di database
        return images_folder

    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_book_page_count(pdf_path):
    """
    Mendapatkan jumlah halaman dari PDF
    """
    try:
        pdf_document = fitz.open(pdf_path)
        page_count = len(pdf_document)
        pdf_document.close()
        print(f"Debug: Page count = {page_count}")
        return page_count
    except Exception as e:
        print(f"Error getting page count: {str(e)}")
        return 0

def get_book_cover_from_pdf(pdf_path, book_id):
    """
    Ekstrak halaman pertama PDF sebagai cover
    """
    try:
        print(f"Debug: Extracting cover from {pdf_path}")

        # Buat folder untuk cover
        covers_folder = "covers"
        covers_dir = os.path.join(settings.MEDIA_ROOT, covers_folder)
        os.makedirs(covers_dir, exist_ok=True)

        # Buka PDF dan ambil halaman pertama
        pdf_document = fitz.open(pdf_path)
        first_page = pdf_document.load_page(0)

        # Konversi ke gambar
        mat = fitz.Matrix(1.5, 1.5)  # 1.5x zoom untuk cover
        pix = first_page.get_pixmap(matrix=mat)

        # Simpan sebagai cover
        cover_filename = f"cover_{book_id}_{uuid.uuid4().hex[:8]}.png"
        cover_path = os.path.join(covers_dir, cover_filename)
        pix.save(cover_path)

        pdf_document.close()
        print(f"Debug: Cover saved to {cover_path}")

        # Return relative path
        return f"covers/{cover_filename}"

    except Exception as e:
        print(f"Error extracting cover: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def extract_text_from_pdf(pdf_path):
    """
    Ekstrak teks dari file PDF dengan berbagai metode fallback
    """
    try:
        print(f"Debug: Extracting text from {pdf_path}")
        pdf_document = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)

            # Metode 1: Ekstrak teks langsung
            text = page.get_text()
            if text.strip():
                full_text += text + " "
                continue

            # Metode 2: Coba ekstrak teks dengan encoding berbeda
            try:
                text = page.get_text("text")
                if text.strip():
                    full_text += text + " "
                    continue
            except:
                pass

            # Metode 3: Coba ekstrak dari text blocks
            try:
                blocks = page.get_text("blocks")
                for block in blocks:
                    if isinstance(block, tuple) and len(block) >= 5:
                        block_text = block[4]  # Teks ada di index ke-4
                        if block_text.strip():
                            full_text += block_text + " "
            except:
                pass

        pdf_document.close()

        extracted_text = full_text.strip()
        print(f"Debug: Extracted {len(extracted_text)} characters from PDF")

        # Jika teks terlalu sedikit, coba ekstrak dari metadata atau buat teks dummy
        if len(extracted_text) < 50:
            print("Debug: Very little text extracted, trying metadata...")

            # Coba baca metadata PDF
            try:
                pdf_document = fitz.open(pdf_path)
                metadata = pdf_document.metadata
                pdf_document.close()

                if metadata:
                    meta_text = ""
                    for key, value in metadata.items():
                        if value and isinstance(value, str):
                            meta_text += f"{value} "

                    if len(meta_text.strip()) > 20:
                        print(f"Debug: Using metadata text: {len(meta_text)} characters")
                        return meta_text.strip()
            except:
                pass

            # Jika masih tidak ada teks, buat keywords berdasarkan nama file
            filename = os.path.basename(pdf_path)
            filename_words = re.sub(r'[^a-zA-Z\s]', ' ', filename).split()
            fallback_text = " ".join([word for word in filename_words if len(word) > 2])

            if fallback_text:
                print(f"Debug: Using filename-based text: {fallback_text}")
                return fallback_text + " document book pdf file text content"

            print("Debug: No text could be extracted from PDF")
            return ""

        return extracted_text

    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""

def clean_text(text):
    """
    Bersihkan dan preprocess teks
    """
    # Hapus karakter non-alfabet dan angka
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Convert ke lowercase
    text = text.lower()
    
    # Hapus extra whitespace
    text = ' '.join(text.split())
    
    return text

def analyze_book_text(pdf_path, max_keywords=10):
    """
    Analisis teks buku untuk mendapatkan kata-kata relevan
    dengan fallback untuk PDF yang sulit diekstrak
    """
    try:
        print(f"Debug: Starting text analysis for {pdf_path}")
        
        # Ekstrak teks dari PDF
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text:
            print("Debug: No text extracted from PDF")
            return []
        
        print(f"Debug: Extracted {len(raw_text)} characters of text")
        
        # Turunkan threshold untuk teks yang sedikit
        if len(raw_text.strip()) < 30:
            print("Debug: Very little text, creating basic keywords from filename")
            # Buat keywords dari nama file dan info buku
            filename = os.path.basename(pdf_path)
            filename_words = re.sub(r'[^a-zA-Z\s]', ' ', filename).split()
            basic_keywords = [word.lower() for word in filename_words if len(word) > 3]
            basic_keywords.extend(['document', 'book', 'content', 'text', 'reading'])
            return basic_keywords[:max_keywords]

        # Bersihkan teks
        clean_text_content = clean_text(raw_text)
        if not clean_text_content:
            print("Debug: No text after cleaning")
            return []

        print(f"Debug: Clean text length: {len(clean_text_content)}")

        # Analisis dengan word frequency
        try:
            # Gunakan split sederhana jika NLTK gagal
            try:
                from nltk.tokenize import word_tokenize
                words = word_tokenize(clean_text_content.lower())
            except:
                print("Debug: NLTK failed, using simple split")
                words = clean_text_content.lower().split()

            # Filter kata-kata
            stop_words = {
                'dan', 'atau', 'yang', 'untuk', 'dengan', 'dari', 'ke', 'di', 'pada',
                'dalam', 'oleh', 'karena', 'sebagai', 'adalah', 'akan', 'dapat',
                'telah', 'tidak', 'ada', 'ini', 'itu', 'juga', 'hanya', 'sudah',
                'masih', 'lebih', 'saja', 'bisa', 'jika', 'bila', 'maka', 'sehingga',
                'namun', 'tetapi', 'bahwa', 'dimana', 'bagaimana', 'kapan', 'siapa',
                'mengapa', 'apa', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'a', 'an', 'as', 'is', 'was', 'are', 'were',
                'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'page', 'pdf'
            }

            # Filter kata yang valid
            filtered_words = []
            for word in words:
                clean_word = re.sub(r'[^a-zA-Z]', '', word)  # Hapus karakter non-alfabet
                if (len(clean_word) > 3 and
                    clean_word.isalpha() and
                    clean_word.lower() not in stop_words):
                    filtered_words.append(clean_word.lower())

            if not filtered_words:
                print("Debug: No valid words found after filtering")
                # Fallback: ambil kata unik dari teks mentah
                raw_words = raw_text.split()
                fallback_words = []
                for word in raw_words:
                    clean_word = re.sub(r'[^a-zA-Z]', '', word)
                    if len(clean_word) > 4 and clean_word.isalpha():
                        fallback_words.append(clean_word.lower())

                if fallback_words:
                    unique_words = list(set(fallback_words))
                    return unique_words[:max_keywords]
                else:
                    return ['document', 'content', 'book', 'text', 'reading']

            # Hitung frekuensi
            word_freq = Counter(filtered_words)

            # Ambil kata-kata paling sering muncul
            common_words = word_freq.most_common(max_keywords * 3)

            # Filter kata dengan frekuensi yang wajar
            keywords = []
            for word, freq in common_words:
                # Turunkan threshold minimal
                if len(word) >= 4:  # Minimal panjang 4 karakter
                    keywords.append(word)
                if len(keywords) >= max_keywords:
                    break

            # Jika masih tidak ada keywords, ambil kata unik yang panjang
            if not keywords:
                unique_words = list(set([
                    word for word in filtered_words
                    if len(word) > 4
                ]))
                keywords = unique_words[:max_keywords]

            print(f"Debug: Found {len(keywords)} keywords: {keywords}")
            return keywords[:max_keywords] if keywords else ['document', 'content', 'text']

        except Exception as e:
            print(f"Debug: Error in word frequency analysis: {str(e)}")

            unique_words = list(set([
                word.lower() for word in words
                if len(word) > 5 and word.isalpha()
            ]))

            return unique_words[:max_keywords] if unique_words else []

    except Exception as e:
        print(f"Error in text analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return []