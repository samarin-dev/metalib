# metalib — Документація / Documentation

> **Free and open-source cross-platform content uniqueizer**
> Автор / Author: Mykhailo Samarin | Ліцензія / License: GPL-3.0
> GitHub: https://github.com/samarin-dev/metalib

---

# 🇺🇦 УКРАЇНСЬКА ВЕРСІЯ

---

## Що таке metalib?

**metalib** — це безкоштовний інструмент з відкритим вихідним кодом, написаний на Python, що призначений для *унікалізації* медіаконтенту (зображень та відео). Його мета — модифікувати файли таким чином, щоб вони відрізнялись на рівні пікселів, метаданих і характеристик зображення, зберігаючи при цьому візуальну ідентичність оригіналу. Це корисно, наприклад, коли потрібно публікувати однаковий контент на різних платформах, уникаючи виявлення дублікатів.

---

## Структура репозиторію

```
metalib/
├── meta-main.py              # Головний скрипт обробки зображень
├── meta-main-vid.py          # Головний скрипт обробки відео
├── meta-blur.py              # Ефект розмиття (зображення)
├── meta-blur-vid.py          # Ефект розмиття (відео)
├── meta-grain.py             # Ефект зерна (зображення)
├── meta-grain-vid.py         # Ефект зерна (відео)
├── meta-sharpen.py           # Ефект різкості (зображення)
├── meta-sharpen-vid.py       # Ефект різкості (відео)
├── meta-text-obfuscator.py   # Текстовий оверлей (зображення)
├── meta-text-obfuscator-vid.py # Текстовий оверлей (відео)
├── cnc-ml.py                 # ML-скрипт (автоенкодер)
├── meta_utils.py             # Спільні утиліти
├── config.ini                # Основний конфігураційний файл
├── presets.ini               # EXIF-пресети камер
├── dictionary.txt            # Словник для текстового оверлею
└── ML/                       # Папка для збереження вагів нейромережі
```

---

## Залежності (встановлення)

Встановіть усі необхідні бібліотеки командою:

```bash
pip install opencv-python numpy torch torch-directml imageio-ffmpeg Pillow piexif
```

| Бібліотека | Призначення |
|---|---|
| `opencv-python` | Обробка зображень та відео |
| `numpy` | Математичні операції з масивами |
| `torch` | Фреймворк для машинного навчання (PyTorch) |
| `torch-directml` | Підтримка GPU на Windows через DirectML |
| `imageio-ffmpeg` | Кодування/декодування відео |
| `Pillow` | Робота з зображеннями (PIL) |
| `piexif` | Читання та запис EXIF-метаданих |

---

## Модулі та їх функціонал

### 1. `meta-main.py` — Головний процесор зображень

Це центральний скрипт для обробки статичних зображень (`.jpg`, `.jpeg`, `.png`, `.webp`).

**Що він робить:**

- Читає зображення з папки `Input/`
- Застосовує ефект артефактів (мертві пікселі, сенсорний шум)
- Змінює розмір і кадрування зображення (опціонально)
- Записує підроблені EXIF-метадані (марка камери, модель, об'єктив, ISO, діафрагма, фокусна відстань, дата/час)
- Зберігає результат у папку `Output/` у форматі JPEG з якістю 95%

**Принцип роботи:**

1. Завантажує налаштування з `config.ini` та пресети з `presets.ini`
2. Для кожного зображення вибирає пресет (фіксований або випадковий)
3. Якщо увімкнено — змінює розмір і обрізає зображення до заданої роздільної здатності зі збереженням пропорцій
4. Якщо увімкнено — додає візуальні артефакти:
   - **Мертві пікселі**: випадкові кольорові точки (червоні, зелені, сині або білі)
   - **Сенсорний шум**: вертикальні смуги — імітація дефектів матриці
5. Генерує EXIF з рандомним зміщенням часу (від 12 до 19 хвилин до поточного часу)
6. Зберігає файл із вбудованими метаданими

---

### 2. `meta-blur.py` / `meta-blur-vid.py` — Ефект розмиття

Застосовує Gaussian blur (розмиття по Гауссу) до зображень або кожного кадру відео.

**Параметри в `config.ini`:**
```ini
[BLUR]
enable_blur = True
blur_radius = 2.5   # Радіус розмиття (0.5 — слабке, 5.0 — сильне)
```

Розмиття змінює унікальний «відбиток» файлу на рівні частот зображення, що ускладнює автоматичне порівняння контенту алгоритмами платформ.

---

### 3. `meta-grain.py` / `meta-grain-vid.py` — Ефект зерна

Додає випадковий цифровий шум (зернистість) — імітує фотографічне зерно плівкових камер або шум матриці.

**Параметри в `config.ini`:**
```ini
[GRAIN]
enable_grain = True
grain_intensity = 0.1   # Інтенсивність (0.1 — ледь помітне, 1.0 — сильне)
```

Зерно вноситься у кожен піксель зображення у вигляді випадкових відхилень яскравості, що робить кожен оброблений файл унікальним.

---

### 4. `meta-sharpen.py` / `meta-sharpen-vid.py` — Підвищення різкості

Застосовує алгоритм підвищення чіткості зображення за допомогою `ImageEnhance` з Pillow.

**Параметри в `config.ini`:**
```ini
[SHARPEN]
enable_sharpen = True
sharpen_factor = 2.1   # 1.0 — оригінал, 2.0 — вдвічі гостріше (рекомендовано: 1.5–3.0)
```

---

### 5. `meta-text-obfuscator.py` / `meta-text-obfuscator-vid.py` — Текстовий оверлей

Накладає на зображення або відео випадковий текст зі словника. Текст напівпрозорий і практично непомітний для людини, але впливає на хеш-суму файлу.

**Параметри в `config.ini`:**
```ini
[TEXT]
enable_text = true
dictionary_path = dictionary.txt   # Шлях до словника
word_count = 6                     # Кількість слів у фразі
anchor = BL                        # Позиція тексту: TL, TC, TR, LC, CC, RC, BL, BC, BR
padding_x_ratio = 0.05             # Відступ по горизонталі (5% ширини)
padding_y_ratio = 0.05             # Відступ по вертикалі (5% висоти)
wrap_width_ratio = 0.7             # Максимальна ширина блоку (70% ширини)
opacity = 0.3                      # Прозорість (0.0 — невидимий, 1.0 — повністю видимий)
stroke_width = 2                   # Ширина контуру символів (пікселі)
font_size = 14                     # Розмір шрифту
; font_path = C:/Windows/Fonts/arial.ttf   # Шлях до шрифту (необов'язково)
```

**Позиції тексту:**
```
TL  TC  TR
LC  CC  RC
BL  BC  BR
```

---

### 6. `cnc-ml.py` — ML-обробка (нейромережа-автоенкодер)

Це найпросунутіший модуль. Він використовує згорткову нейромережу типу **автоенкодер** на базі PyTorch для трансформації зображень та відео.

**Принцип роботи автоенкодера:**

```
Вхідне зображення → [Енкодер: стискання до латентного простору] → [Декодер: відновлення] → Вихідне зображення
```

Нейромережа вчиться "перекодовувати" зображення: стискати їх до компактного внутрішнього представлення і відновлювати назад. У процесі відновлення з'являються характерні відмінності від оригіналу, що робить кожне зображення унікальним.

**Архітектура мережі:**
- **Енкодер**: 4 шари Conv2d зі stride=2 (зменшення розміру в 16 разів), BatchNorm, ReLU
- **Декодер**: 4 шари ConvTranspose2d (відновлення до оригінального розміру), Sigmoid на виході

**Режими роботи:**

| Команда | Опис |
|---|---|
| `python cnc-ml.py` | Обробка файлів з `input/` (потрібні збережені ваги) |
| `python cnc-ml.py --learn` | Тренування мережі на файлах з `input/` |
| `python cnc-ml.py --cuda` | Використання NVIDIA GPU (CUDA) |
| `python cnc-ml.py --directml` | Використання AMD/Intel GPU через DirectML (Windows) |
| `python cnc-ml.py --device cuda:0` | Явне задання пристрою |

**Параметри тренування (у коді):**
```python
IMG_SIZE = 256      # Розмір зображення для тренування
EPOCHS = 10         # Кількість епох навчання
LEARNING_RATE = 0.001
BATCH_SIZE = 16
```

Ваги зберігаються у `ML/autoencoder.pth` та автоматично завантажуються при наступному запуску.

**Підтримувані формати:**
- Зображення: `.jpg`, `.jpeg`, `.png`, `.bmp`
- Відео: `.mp4`, `.avi`, `.mov`, `.mkv`

---

## Конфігурація

### `config.ini` — Основний файл налаштувань

```ini
[GENERAL]
input_dir = Input     # Папка з вхідними файлами
output_dir = Output   # Папка для збереження результатів

[RESOLUTION]
enable_resizing = False   # Увімкнути зміну роздільної здатності
mode = portrait           # landscape або portrait
width = 4032
height = 3024

[EFFECTS]
enable_artifacts = True       # Артефакти (мертві пікселі, шум)
dead_pixels_count = 10        # Кількість мертвих пікселів
sensor_stripes_count = 0      # Кількість вертикальних смуг шуму

[PRESETS]
current_preset = random   # Назва пресету або "random" для випадкового вибору
```

### `presets.ini` — EXIF-пресети

Кожен пресет описує параметри конкретної камери, які будуть записані в EXIF оброблених зображень:

```ini
[iPhone14]
make = Apple
model = iPhone 14
lens = iPhone 14 back main camera 5.7mm f/1.5
f_number = 1.5
focal_length = 5.7
software = 17.4.1

[iPhone13]
make = Apple
model = iPhone 13
...
```

Ви можете додавати власні пресети для будь-яких камер. При значенні `current_preset = random` система випадково обирає один із наявних пресетів для кожного файлу.

---

## Покрокова інструкція використання

### Крок 1: Клонування репозиторію

```bash
git clone https://github.com/samarin-dev/metalib.git
cd metalib
```

### Крок 2: Встановлення залежностей

```bash
pip install opencv-python numpy torch torch-directml imageio-ffmpeg Pillow piexif
```

### Крок 3: Підготовка файлів

Помістіть зображення або відео, що потребують обробки, у папку `Input/` (або `input/` для ML-скрипту). Якщо папки не існує — створіть її вручну або запустіть скрипт (він створить її автоматично).

### Крок 4: Налаштування config.ini

Відкрийте `config.ini` і налаштуйте потрібні параметри. Наприклад, для мінімальної обробки лише з EXIF-заміною:

```ini
[EFFECTS]
enable_artifacts = False

[BLUR]
enable_blur = False

[SHARPEN]
enable_sharpen = False

[GRAIN]
enable_grain = False

[TEXT]
enable_text = false
```

### Крок 5: Запуск потрібного скрипту

```bash
# Основна обробка зображень (EXIF + артефакти)
python meta-main.py

# Тільки розмиття
python meta-blur.py

# Тільки зерно
python meta-grain.py

# Тільки підвищення різкості
python meta-sharpen.py

# Текстовий оверлей
python meta-text-obfuscator.py

# Аналогічно для відео — додайте -vid до назви:
python meta-main-vid.py
python meta-blur-vid.py
# і т.д.

# ML-обробка (спочатку тренування, потім — застосування):
python cnc-ml.py --learn        # тренування
python cnc-ml.py                # застосування
python cnc-ml.py --cuda         # з NVIDIA GPU
```

### Крок 6: Отримання результату

Оброблені файли з'являться в папці `Output/`.

---

## Типові сценарії використання

**Сценарій 1 — Масова унікалізація зображень для соціальних мереж:**
```ini
[PRESETS]
current_preset = random   # різні камери для кожного фото

[EFFECTS]
enable_artifacts = True
dead_pixels_count = 5

[GRAIN]
enable_grain = True
grain_intensity = 0.05   # ледь помітне зерно
```

**Сценарій 2 — Максимальна унікалізація з ML:**
```bash
# 1. Покладіть оригінали в input/
# 2. Запустіть тренування
python cnc-ml.py --learn --cuda
# 3. Після тренування — обробіть
python cnc-ml.py --cuda
```

---

## Додавання власних EXIF-пресетів

Відкрийте `presets.ini` і додайте новий розділ:

```ini
[SamsungS24]
make = Samsung
model = SM-S921B
lens = Samsung S24 rear camera 6.3mm f/1.8
f_number = 1.8
focal_length = 6.3
software = OneUI 6.1
```

Після збереження файлу пресет стане доступним. Щоб використати його — вкажіть `current_preset = SamsungS24` у `config.ini`.

---

---

# 🇬🇧 ENGLISH VERSION

---

## What is metalib?

**metalib** is a free, open-source Python toolkit for *content uniqueization* — the process of modifying media files (images and videos) so that each output copy differs from the original at the pixel, metadata, and signal levels, while remaining visually identical. This is useful when publishing the same content across multiple platforms that use duplicate-detection algorithms.

---

## Repository Structure

```
metalib/
├── meta-main.py              # Main image processor
├── meta-main-vid.py          # Main video processor
├── meta-blur.py              # Blur effect (images)
├── meta-blur-vid.py          # Blur effect (video)
├── meta-grain.py             # Grain effect (images)
├── meta-grain-vid.py         # Grain effect (video)
├── meta-sharpen.py           # Sharpening effect (images)
├── meta-sharpen-vid.py       # Sharpening effect (video)
├── meta-text-obfuscator.py   # Text overlay (images)
├── meta-text-obfuscator-vid.py # Text overlay (video)
├── cnc-ml.py                 # ML script (autoencoder)
├── meta_utils.py             # Shared utilities
├── config.ini                # Main configuration file
├── presets.ini               # Camera EXIF presets
├── dictionary.txt            # Word dictionary for text overlay
└── ML/                       # Folder for neural network weights
```

---

## Dependencies (Installation)

Install all required libraries with:

```bash
pip install opencv-python numpy torch torch-directml imageio-ffmpeg Pillow piexif
```

| Library | Purpose |
|---|---|
| `opencv-python` | Image and video processing |
| `numpy` | Array math operations |
| `torch` | PyTorch ML framework |
| `torch-directml` | AMD/Intel GPU support on Windows via DirectML |
| `imageio-ffmpeg` | Video encoding/decoding |
| `Pillow` | Image manipulation (PIL) |
| `piexif` | EXIF metadata read/write |

---

## Modules and Their Functionality

### 1. `meta-main.py` — Main Image Processor

The central script for processing static images (`.jpg`, `.jpeg`, `.png`, `.webp`).

**What it does:**

- Reads images from the `Input/` folder
- Optionally applies artifact effects (dead pixels, sensor noise)
- Optionally resizes and crops images
- Writes fake EXIF metadata (camera make, model, lens, ISO, aperture, focal length, timestamp)
- Saves results to `Output/` as JPEG with 95% quality

**How it works:**

1. Loads settings from `config.ini` and presets from `presets.ini`
2. For each image, selects a preset (fixed or random)
3. If enabled — resizes and center-crops the image to the target resolution while maintaining aspect ratio
4. If enabled — adds visual artifacts:
   - **Dead pixels**: random colored dots (red, green, blue, or white)
   - **Sensor noise stripes**: vertical lines simulating sensor defects
5. Generates EXIF data with a random time offset (12–19 minutes before the current time)
6. Saves the file with embedded metadata

---

### 2. `meta-blur.py` / `meta-blur-vid.py` — Blur Effect

Applies Gaussian blur to images or each frame of a video.

**Parameters in `config.ini`:**
```ini
[BLUR]
enable_blur = True
blur_radius = 2.5   # Blur radius (0.5 = subtle, 5.0 = heavy)
```

Blur alters the image's frequency-domain fingerprint, making automated content-matching algorithms less likely to identify it as a duplicate.

---

### 3. `meta-grain.py` / `meta-grain-vid.py` — Grain Effect

Adds random digital noise (grain) that simulates film grain or camera sensor noise.

**Parameters in `config.ini`:**
```ini
[GRAIN]
enable_grain = True
grain_intensity = 0.1   # Intensity (0.1 = barely visible, 1.0 = heavy)
```

Grain is applied as random brightness variations per pixel, making each processed file unique at the binary level.

---

### 4. `meta-sharpen.py` / `meta-sharpen-vid.py` — Sharpening

Enhances image sharpness using Pillow's `ImageEnhance` module.

**Parameters in `config.ini`:**
```ini
[SHARPEN]
enable_sharpen = True
sharpen_factor = 2.1   # 1.0 = original, 2.0 = double sharpness (recommended: 1.5–3.0)
```

---

### 5. `meta-text-obfuscator.py` / `meta-text-obfuscator-vid.py` — Text Overlay

Overlays random words from a dictionary file onto images or video frames. The text is semi-transparent and nearly invisible to the human eye, but alters the file's binary signature.

**Parameters in `config.ini`:**
```ini
[TEXT]
enable_text = true
dictionary_path = dictionary.txt   # Path to word dictionary
word_count = 6                     # Words per random phrase
anchor = BL                        # Text position: TL, TC, TR, LC, CC, RC, BL, BC, BR
padding_x_ratio = 0.05             # Horizontal padding (5% of image width)
padding_y_ratio = 0.05             # Vertical padding (5% of image height)
wrap_width_ratio = 0.7             # Max text block width (70% of image width)
opacity = 0.3                      # Opacity (0.0 = invisible, 1.0 = fully opaque)
stroke_width = 2                   # Character outline width (pixels)
font_size = 14                     # Font size
; font_path = C:/Windows/Fonts/arial.ttf   # Optional explicit font path
```

**Text anchor positions:**
```
TL  TC  TR
LC  CC  RC
BL  BC  BR
```

---

### 6. `cnc-ml.py` — ML Processing (Autoencoder Neural Network)

The most advanced module. It uses a **convolutional autoencoder** neural network built with PyTorch to transform images and videos.

**How the autoencoder works:**

```
Input image → [Encoder: compress to latent space] → [Decoder: reconstruct] → Output image
```

The network learns to "recode" images: compress them to a compact internal representation and reconstruct them. In the reconstruction process, subtle differences from the original emerge, making each output unique.

**Network Architecture:**
- **Encoder**: 4× Conv2d layers with stride=2 (16× spatial reduction), BatchNorm, ReLU activations
- **Decoder**: 4× ConvTranspose2d layers (restores original resolution), Sigmoid output activation

**Operating Modes:**

| Command | Description |
|---|---|
| `python cnc-ml.py` | Process files from `input/` (requires saved weights) |
| `python cnc-ml.py --learn` | Train the network on files from `input/` |
| `python cnc-ml.py --cuda` | Use NVIDIA GPU (CUDA) |
| `python cnc-ml.py --directml` | Use AMD/Intel GPU via DirectML (Windows) |
| `python cnc-ml.py --device cuda:0` | Specify device explicitly |

**Training parameters (in code):**
```python
IMG_SIZE = 256      # Training image size
EPOCHS = 10         # Number of training epochs
LEARNING_RATE = 0.001
BATCH_SIZE = 16
```

Weights are saved to `ML/autoencoder.pth` and automatically loaded on the next run.

**Supported formats:**
- Images: `.jpg`, `.jpeg`, `.png`, `.bmp`
- Video: `.mp4`, `.avi`, `.mov`, `.mkv`

---

## Configuration

### `config.ini` — Main Settings File

```ini
[GENERAL]
input_dir = Input     # Folder with input files
output_dir = Output   # Folder for output files

[RESOLUTION]
enable_resizing = False   # Enable resolution change
mode = portrait           # landscape or portrait
width = 4032
height = 3024

[EFFECTS]
enable_artifacts = True       # Enable artifacts (dead pixels, noise)
dead_pixels_count = 10        # Number of dead pixels
sensor_stripes_count = 0      # Number of vertical noise stripes

[PRESETS]
current_preset = random   # Preset name or "random" for random selection
```

### `presets.ini` — EXIF Camera Presets

Each preset describes camera parameters that will be embedded into the EXIF metadata of processed images:

```ini
[iPhone14]
make = Apple
model = iPhone 14
lens = iPhone 14 back main camera 5.7mm f/1.5
f_number = 1.5
focal_length = 5.7
software = 17.4.1

[iPhone13]
make = Apple
model = iPhone 13
...
```

You can add your own presets for any camera. When `current_preset = random`, the system randomly selects one of the available presets for each file.

---

## Step-by-Step Usage Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/samarin-dev/metalib.git
cd metalib
```

### Step 2: Install Dependencies

```bash
pip install opencv-python numpy torch torch-directml imageio-ffmpeg Pillow piexif
```

### Step 3: Prepare Input Files

Place the images or videos you want to process in the `Input/` folder (or `input/` for the ML script). If the folder does not exist, create it manually or run the script — it will create the folder automatically.

### Step 4: Configure config.ini

Open `config.ini` and adjust settings as needed. For example, for minimal processing (EXIF replacement only):

```ini
[EFFECTS]
enable_artifacts = False

[BLUR]
enable_blur = False

[SHARPEN]
enable_sharpen = False

[GRAIN]
enable_grain = False

[TEXT]
enable_text = false
```

### Step 5: Run the Desired Script

```bash
# Main image processing (EXIF + artifacts)
python meta-main.py

# Blur only
python meta-blur.py

# Grain only
python meta-grain.py

# Sharpen only
python meta-sharpen.py

# Text overlay
python meta-text-obfuscator.py

# Video equivalents — append -vid to the name:
python meta-main-vid.py
python meta-blur-vid.py
# etc.

# ML processing (train first, then apply):
python cnc-ml.py --learn        # training
python cnc-ml.py                # inference
python cnc-ml.py --cuda         # with NVIDIA GPU
```

### Step 6: Collect Results

Processed files will appear in the `Output/` folder.

---

## Common Use Case Scenarios

**Scenario 1 — Bulk uniqueization of images for social media:**
```ini
[PRESETS]
current_preset = random   # different camera metadata per photo

[EFFECTS]
enable_artifacts = True
dead_pixels_count = 5

[GRAIN]
enable_grain = True
grain_intensity = 0.05   # barely visible grain
```

**Scenario 2 — Maximum uniqueization with ML:**
```bash
# 1. Place originals in input/
# 2. Train the network
python cnc-ml.py --learn --cuda
# 3. After training, process
python cnc-ml.py --cuda
```

---

## Adding Your Own EXIF Presets

Open `presets.ini` and add a new section:

```ini
[SamsungS24]
make = Samsung
model = SM-S921B
lens = Samsung S24 rear camera 6.3mm f/1.8
f_number = 1.8
focal_length = 6.3
software = OneUI 6.1
```

After saving, the preset becomes available. To use it, set `current_preset = SamsungS24` in `config.ini`.

---

## License

metalib is distributed under the **GNU General Public License v3.0 (GPL-3.0)**. You are free to use, modify, and distribute the software provided you retain the original license and attribution.
