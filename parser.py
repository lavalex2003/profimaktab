from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List


def parse_dairy(dairy: List[Dict[str, Any]], *, student: str, date: str) -> Dict[str, Any]:
    lessons = []
    marks: List[int] = []

    for item in sorted(dairy, key=lambda x: x.get("lesson_order", 0)):
        subject = item.get("subject", {}).get("name")
        themes = item.get("themes") or []
        topic = themes[0]["title"] if themes else None
        homework = themes[0].get("notes") if themes else None

        mark_value = None
        mark_reason = None
        if item.get("marks"):
            m = item["marks"][0]
            mark_value = str(m.get("value"))
            mark_reason = m.get("reason")
            try:
                marks.append(int(mark_value))
            except Exception:
                pass

        lessons.append(
            {
                "lesson": item.get("lesson_order"),
                "subject": subject,
                "topic": topic,
                "homework": homework,
                "mark": (
                    {"value": mark_value, "reason": mark_reason}
                    if mark_value
                    else None
                ),
            }
        )

    avg = round(mean(marks), 1) if marks else 0

    return {
        "date": date,
        "student": student,
        "lessons": lessons,
        "lesson_count": len(lessons),
        "marks": marks,
        "marks_count": len(marks),
        "average": avg,
    }
