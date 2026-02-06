# ProfiMaktab

Custom Home Assistant integration for ProfiMaktab (Uzbekistan school platform).

## Features
- Config Flow (UI setup)
- Multiple students support (1 Config Entry = 1 student)
- Manual update via global button
- No polling
- Dispatcher-based updates
- Data for current day only
- Home Assistant history support

## Installation

### HACS
1. Add this repository to HACS as a custom repository
2. Category: Integration
3. Install **ProfiMaktab**
4. Restart Home Assistant

### Manual
Copy `custom_components/profimaktab` to your Home Assistant `custom_components` directory.

## Configuration
Configured via Home Assistant UI:
- Username
- Password
- Student / profile selection

## Supported languages
- English
- Russian
- Uzbek

## Notes
This integration does not use polling.
Data is updated only on setup and by pressing the update button.

---

Developed for Home Assistant Core 2026.x
