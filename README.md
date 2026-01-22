# ProfiMaktab Home Assistant Integration

Custom Home Assistant integration for **profimaktab.uz** — electronic school diary.

## ✨ Features

- 📚 Fetches **daily school data** for the current day
- 👶 Supports **multiple children**
  - 1 Config Entry = 1 child
- 🔐 Authentication via **username / password**
  - Access token (Bearer) handled internally
- 🔘 **Single global update button**
  - Updates data for **all children**
- 🚫 No polling
  - Data updates **only on setup** and **on button press**
- ⚡ Fully async, Home Assistant Core **2026.x compatible**
- 🧠 History stored via Home Assistant Recorder

---

## 🧩 Entities

### Sensors (per child)

#### `sensor.school_day_<name>`
- **State:** `YYYY-MM-DD`
- **Attributes:**
  - `student`
  - `lesson_count`
  - `lessons` (normalized JSON)
  - `source`
  - `attribution`

#### `sensor.average_mark_<name>`
- **State:** average mark for the day
- **Attributes:**
  - `student`
  - `marks`
  - `marks_count`
  - `date`
  - `source`
  - `attribution`

---

### Button (global)

#### `button.update_profimaktab_data`
- Updates data for **all configured children**
- Always requests: /diary/?for_date=today

---

## ⚙️ Installation

### HACS (recommended)

1. Open **HACS**
2. Go to **Integrations**
3. Add custom repository: https://github.com/lavalex2003/profimaktab
4. Install **ProfiMaktab**
5. Restart Home Assistant

---

## 🔧 Configuration

Configured **only via UI**:

1. Go to **Settings → Devices & Services**
2. Add integration **ProfiMaktab**
3. Enter:
- Username
- Password
- Child name (if requested)

Repeat for each child.

---

## 🧠 Architecture Notes

- No polling
- Dispatcher-based updates
- Thread-safe state updates
- One global button per integration domain
- Designed according to Home Assistant best practices (2026.x)

---

## 📝 Notes

- Only **current day** data is fetched
- Historical data is stored automatically by Home Assistant
- Integration does not create background tasks or schedulers

---

## 📄 License

MIT
