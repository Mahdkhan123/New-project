from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QInputDialog,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QHeaderView, QDialog, QLineEdit,
    QDateEdit, QTimeEdit, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QTextDocument
from PyQt6.QtPrintSupport import QPrinter
import os
import sqlite3
from PyQt6.QtWidgets import QInputDialog, QMessageBox
from algorithm.datesheet_ga import DatesheetGeneticAlgorithm
import pandas as pd
from datetime import datetime

class DatesheetWindow(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Tab widget for semester frames
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_semester_tab)
        main_layout.addWidget(self.tab_widget)

        # Bottom buttons (always visible)
        bottom_buttons = self.create_bottom_buttons()
        main_layout.addWidget(bottom_buttons)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #2196F3; color: white;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("Datesheet Data Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        home_btn = QPushButton("Home")
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        if self.back_callback:
            home_btn.clicked.connect(self.back_callback)
        # Add "Add Semester" button
        add_semester_btn = QPushButton("Add Semester")
        add_semester_btn.setStyleSheet(self.get_button_style("#007bff", min_width="150px"))
        add_semester_btn.clicked.connect(self.add_new_semester_dialog)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_semester_btn)
        header_layout.addWidget(home_btn)
        return header

    def add_new_semester_dialog(self):
        name, ok = QInputDialog.getText(self, "New Semester Frame", "Enter semester:")
        if ok and name.strip():
            self.add_semester_tab(name.strip())

    def add_semester_tab(self, semester_name):
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QComboBox, QCheckBox, QTableWidgetItem, QHeaderView
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_header_layout = QHBoxLayout()
        title = QLabel("Datesheet Entries")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 15px;")
        add_row_btn = QPushButton("Add New Entry")
        add_row_btn.setStyleSheet(self.get_button_style("#007bff", min_width="150px"))
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "", "#", "Shift", "Semester", "Class/Section", "Room",
            "Teacher Name", "Course Code", "Course Name", "Lab"
        ])
        table.horizontalHeader().setVisible(True)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(40)
        header_view = table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 50)
        table.setColumnWidth(1, 40)

        def add_row():
            row_position = table.rowCount()
            table.insertRow(row_position)

            # --- Copy data from previous row if exists ---
            prev_data = {}
            if row_position > 0:
                # Shift (QComboBox)
                prev_shift = table.cellWidget(row_position - 1, 2)
                if prev_shift:
                    prev_data['shift'] = prev_shift.currentText()
                # Semester, Class/Section, Room (QTableWidgetItem)
                for col, key in zip([3, 4, 5], ['semester', 'class_section', 'room']):
                    prev_item = table.item(row_position - 1, col)
                    if prev_item:
                        prev_data[key] = prev_item.text()
            # ---------------------------------------------

            checkbox = QCheckBox()
            cell_widget_container = QWidget()
            layout = QHBoxLayout(cell_widget_container)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            table.setCellWidget(row_position, 0, cell_widget_container)

            row_num_item = QTableWidgetItem(str(row_position + 1))
            row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_position, 1, row_num_item)

            shift_combo = QComboBox()
            shift_combo.addItems(["Morning", "Evening"])
            shift_combo.setStyleSheet(self.get_combo_style())
            shift_combo.setCurrentText(prev_data.get('shift', "Select Shift"))
            table.setCellWidget(row_position, 2, shift_combo)

            placeholders = {
                3: "Semester",
                4: "Class/Section",
                5: "Room",
                6: "Teacher Name",
                7: "Course Code",
                8: "Course Name",
                9: "Lab"
            }
            for col in range(3, table.columnCount()):
                if col == 3:
                    text = prev_data.get('semester', placeholders[col])
                elif col == 4:
                    text = prev_data.get('class_section', placeholders[col])
                elif col == 5:
                    text = prev_data.get('room', placeholders[col])
                else:
                    text = placeholders.get(col, "")
                item = QTableWidgetItem(text)
                if col in [3, 4, 5] and text != placeholders[col]:
                    item.setForeground(Qt.GlobalColor.black)
                else:
                    item.setForeground(Qt.GlobalColor.gray)
                table.setItem(row_position, col, item)

        add_row_btn.clicked.connect(add_row)
        table_header_layout.addWidget(title)
        table_header_layout.addStretch()
        table_header_layout.addWidget(add_row_btn)
        table_layout.addLayout(table_header_layout)
        table_layout.addWidget(table)
        table_frame.table = table
        self.tab_widget.addTab(table_frame, semester_name)
        self.tab_widget.setCurrentWidget(table_frame)  # Switch to new tab

    def get_current_table(self):
        current_widget = self.tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, "table"):
            return current_widget.table
        return None

    def close_semester_tab(self, index):
        self.tab_widget.removeTab(index)

    def get_combo_style(self):
        return """
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                 border: none;
            }
        """

    def get_button_style(self, color, min_width="120px"):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: {min_width};
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
        """

    def create_bottom_buttons(self):
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        delete_btn = QPushButton("Delete Selected Entries")
        delete_btn.setStyleSheet(self.get_button_style("#dc3545", min_width="180px"))
        clear_btn = QPushButton("Clear All Entries")
        clear_btn.setStyleSheet(self.get_button_style("#6c757d", min_width="150px"))
        load_db_btn = QPushButton("Load from DB")
        load_db_btn.setStyleSheet(self.get_button_style("#007bff", min_width="150px"))
        generate_btn = QPushButton("Generate Datesheet")
        generate_btn.setStyleSheet(self.get_button_style("#17a2b8", min_width="180px"))
        generate_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addSpacing(20)
        buttons_layout.addWidget(load_db_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(generate_btn)
        # Connect your button slots here
        delete_btn.clicked.connect(self.delete_selected_entries)
        clear_btn.clicked.connect(self.clear_all_entries)
        load_db_btn.clicked.connect(self.load_from_db)
        generate_btn.clicked.connect(self.generate_datesheet_dialog)  # Implement as needed
        return buttons_frame

    def delete_selected_entries(self):
        table = self.get_current_table()
        if not table:
            return
        # Collect rows with checked checkboxes in column 0
        rows_to_delete = []
        for row in range(table.rowCount()):
            cell_widget = table.cellWidget(row, 0)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    rows_to_delete.append(row)
        # Remove from bottom to top to avoid row shifting
        for row in reversed(rows_to_delete):
            table.removeRow(row)
        # Re-number the row numbers
        for row in range(table.rowCount()):
            item = table.item(row, 1)
            if item:
                item.setText(str(row + 1))

    def clear_all_entries(self):
        table = self.get_current_table()
        if not table:
            return
        table.setRowCount(0)

    def load_from_db(self):
        # 1. Ask for shift
        shifts = ["All", "Morning", "Evening"]
        shift, ok = QInputDialog.getItem(self, "Select Shift", "Which shift data to display?", shifts, 0, False)
        if not ok:
            return

        # 2. Ask for lab entries
        lab_reply = QMessageBox.question(
            self, "Include Labs?", "Display lab entries as well?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        include_labs = lab_reply == QMessageBox.StandardButton.Yes

        # --- 3. Load data using timetable_db (per-shift DBs) ---
        import sys, importlib.util
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
        timetable_db_path = os.path.join(db_dir, "timetable_db.py")
        spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
        timetable_db = importlib.util.module_from_spec(spec)
        sys.modules["timetable_db"] = timetable_db
        spec.loader.exec_module(timetable_db)

        # collect rows from the selected shift(s)
        shifts_to_load = ["Morning", "Evening"] if shift == "All" else [shift]
        rows = []
        try:
            for s in shifts_to_load:
                entries = timetable_db.load_timetable(s)
                for e in entries:
                    indicators = e.get('course_indicators') or ""
                    # apply lab filter
                    if not include_labs and indicators.strip():
                        continue
                    rows.append((
                        e.get('shift'),
                        e.get('semester'),
                        e.get('class_section_name'),
                        e.get('room_name'),
                        e.get('teacher_name'),
                        e.get('course_code'),
                        e.get('course_name'),
                        indicators
                    ))
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
            return

        # 4. Organize by (shift, semester, class_section)
        tabs_data = {}  # key: (shift, semester, class_section), value: list of rows
        for row in rows:
            shift_val, semester, class_section, room, teacher_name, course_code, course_name, indicators = row
            key = (shift_val, semester, class_section)
            if key not in tabs_data:
                tabs_data[key] = []
            tabs_data[key].append({
                "shift": shift_val,
                "semester": semester,
                "class_section": class_section,
                "room": room,
                "teacher_name": teacher_name,
                "course_code": course_code,
                "course_name": course_name,
                "is_lab": bool(indicators and indicators.strip())
            })

        # 5. Clear all tabs
        self.tab_widget.clear()

        # 6. Create tabs and fill tables (unchanged)
        for (shift_val, semester, class_section), entries in tabs_data.items():
            tab_name = f"{semester} - {class_section} ({shift_val})"
            self.add_semester_tab(tab_name)
            table = self.get_current_table()
            table.setRowCount(0)
            for idx, entry in enumerate(entries):
                table.insertRow(idx)
                # Checkbox
                checkbox = QCheckBox()
                cell_widget_container = QWidget()
                layout = QHBoxLayout(cell_widget_container)
                layout.addWidget(checkbox)
                layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0,0,0,0)
                table.setCellWidget(idx, 0, cell_widget_container)
                # Row number
                row_num_item = QTableWidgetItem(str(idx + 1))
                row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(idx, 1, row_num_item)
                # Shift
                shift_combo = QComboBox()
                shift_combo.addItems(["Morning", "Evening"])
                shift_combo.setStyleSheet(self.get_combo_style())
                shift_combo.setCurrentText(entry["shift"])
                table.setCellWidget(idx, 2, shift_combo)
                # Semester
                sem_item = QTableWidgetItem(entry["semester"])
                sem_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 3, sem_item)
                # Class/Section
                cs_item = QTableWidgetItem(entry["class_section"])
                cs_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 4, cs_item)
                # Room
                room_item = QTableWidgetItem(str(entry["room"]))
                room_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 5, room_item)
                # Teacher Name
                teacher_item = QTableWidgetItem(entry["teacher_name"])
                teacher_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 6, teacher_item)
                # Course Code
                code_item = QTableWidgetItem(entry["course_code"])
                code_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 7, code_item)
                # Course Name
                cname_item = QTableWidgetItem(entry["course_name"])
                cname_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 8, cname_item)
                # Lab
                lab_item = QTableWidgetItem("Lab" if entry["is_lab"] else "")
                lab_item.setForeground(Qt.GlobalColor.black)
                table.setItem(idx, 9, lab_item)

    def generate_datesheet_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Date Sheet Generation")
        dialog.resize(600, 500)
        layout = QVBoxLayout(dialog)

        # --- Metadata Section ---
        meta_label = QLabel("<b>Date Sheet Metadata</b>")
        meta_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(meta_label)

        college_name_edit = QLineEdit("GOVT. ISLAMIA GRADUATE COLLEGE, CIVIL LINES, LAHORE")
        title_edit = QLineEdit("DATE SHEET FOR BS PROGRAMS")
        effective_date_edit = QLineEdit("")
        department_edit = QLineEdit("DEPARTMENT OF COMPUTER SCIENCE")

        layout.addWidget(QLabel("College Name:"))
        layout.addWidget(college_name_edit)
        layout.addWidget(QLabel("Date Sheet Title:"))
        layout.addWidget(title_edit)
        layout.addWidget(QLabel("Effective Date (DD-MM-YYYY):"))
        layout.addWidget(effective_date_edit)
        layout.addWidget(QLabel("Department Name:"))
        layout.addWidget(department_edit)

        # --- Generation Parameters ---
        layout.addWidget(QLabel("<b>Generation Parameters</b>"))

        start_date_edit = QDateEdit()
        start_date_edit.setCalendarPopup(True)
        start_date_edit.setDate(QDate.currentDate())
        exam_start_time_edit = QTimeEdit()
        exam_start_time_edit.setTime(QTime(9, 0))
        exam_end_time_edit = QTimeEdit()
        exam_end_time_edit.setTime(QTime(13, 0))

        layout.addWidget(QLabel("Exam Start Date:"))
        layout.addWidget(start_date_edit)
        layout.addWidget(QLabel("Exam Start Time:"))
        layout.addWidget(exam_start_time_edit)
        layout.addWidget(QLabel("Exam End Time:"))
        layout.addWidget(exam_end_time_edit)

        # Days of the week
        layout.addWidget(QLabel("Exam Days:"))
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_checks = []
        day_layout = QHBoxLayout()
        for day in days:
            cb = QCheckBox(day)
            cb.setChecked(True)
            day_checks.append(cb)
            day_layout.addWidget(cb)
        layout.addLayout(day_layout)

        # Excluded Dates
        layout.addWidget(QLabel("Additional Excluded Dates (comma-separated YYYY-MM-DD):"))
        excluded_dates_edit = QLineEdit()
        layout.addWidget(excluded_dates_edit)

        # --- Dialog Buttons ---
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        generate_btn = QPushButton("Generate")
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(generate_btn)
        layout.addLayout(btn_layout)

        cancel_btn.clicked.connect(dialog.reject)

        def to_24h(qtime_edit):
            return qtime_edit.time().toString("HH:mm")

        def collect_entries():
            # Gather all entries from all tabs
            entries = []
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, "table"):
                    table = tab.table
                    for row in range(table.rowCount()):
                        entry = {
                            "shift": table.cellWidget(row, 2).currentText() if table.cellWidget(row, 2) else "",
                            "semester": table.item(row, 3).text() if table.item(row, 3) else "",
                            "class_section": table.item(row, 4).text() if table.item(row, 4) else "",
                            "room": table.item(row, 5).text() if table.item(row, 5) else "",
                            "teacher": table.item(row, 6).text() if table.item(row, 6) else "",
                            "course_code": table.item(row, 7).text() if table.item(row, 7) else "",
                            "course_name": table.item(row, 8).text() if table.item(row, 8) else "",
                        }
                        # Only add if required fields are present
                        if entry["semester"] and entry["class_section"] and entry["course_name"]:
                            entries.append({
                                "subject": entry["course_name"],
                                "room": entry["room"],
                                "shift": entry["shift"],
                                "semester": entry["semester"],
                                "teacher": entry["teacher"],
                                "course_code": entry["course_code"],
                                "class_section": entry["class_section"]
                            })
            return entries

        def show_preview(metadata, schedule, exam_start_time, exam_end_time):
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("Optimized Datesheet Preview")
            preview_dialog.resize(900, 600)
            vbox = QVBoxLayout(preview_dialog)

            # Store the data for export functions
            preview_dialog.metadata = metadata
            preview_dialog.schedule = schedule
            preview_dialog.exam_time_range = f"{exam_start_time} - {exam_end_time}"

            # Metadata
            vbox.addWidget(QLabel(f"<b>{metadata['college_name']}</b>"))
            vbox.addWidget(QLabel(metadata['datesheet_title']))
            vbox.addWidget(QLabel(f"Effective Date: {metadata['effective_date']}"))
            vbox.addWidget(QLabel(f"Department: {metadata['department_name']}"))

            # Tabbed preview by date
            tab_widget = QTabWidget()
            from collections import defaultdict
            import datetime
            grouped = defaultdict(list)
            for exam in schedule:
                grouped[exam.get("date", "N/A")].append(exam)
            sorted_dates = sorted(grouped.keys(), key=lambda d: d if d == "N/A" else datetime.datetime.strptime(d, "%Y-%m-%d"))
            for date_str in sorted_dates:
                exams = grouped[date_str]
                tab = QWidget()
                tab_layout = QVBoxLayout(tab)
                table = QTableWidget()
                table.setColumnCount(10)
                table.setHorizontalHeaderLabels([
                    "Semester", "Subject", "Course Code", "Class Section", "Day", "Date", "Time", "Room", "Shift", "Teacher (Invigilator)"
                ])
                table.setRowCount(len(exams))
                for row, e in enumerate(exams):
                    # Day name
                    try:
                        day_name = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
                    except Exception:
                        day_name = "N/A"
                    # Time range
                    start_ampm = QTime.fromString(e.get("time", exam_start_time), "HH:mm").toString("hh:mm AP")
                    end_ampm = QTime.fromString(exam_end_time, "HH:mm").toString("hh:mm AP")
                    time_range = f"{start_ampm} - {end_ampm}"
                    values = [
                        e.get("semester", ""),
                        e.get("subject", ""),
                        e.get("course_code", ""),
                        e.get("class_section", ""),
                        day_name,
                        date_str,
                        time_range,
                        e.get("room", ""),
                        e.get("shift", ""),
                        e.get("teacher", "")
                    ]
                    for col, val in enumerate(values):
                        table.setItem(row, col, QTableWidgetItem(str(val)))
                table.resizeColumnsToContents()
                tab_layout.addWidget(table)
                tab_widget.addTab(tab, f"{date_str} ({day_name})")
            vbox.addWidget(tab_widget)

            # Add export buttons
            export_layout = QHBoxLayout()
            export_to_pdf = QPushButton("Export to PDF")
            export_to_excel = QPushButton("Export to Excel")
            
            # Updated button styling
            button_style = """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 14px;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """
            
            excel_button_style = button_style.replace("#4CAF50", "#2196F3").replace("#45a049", "#1976D2").replace("#3d8b40", "#1565C0")
            
            export_to_pdf.setStyleSheet(button_style)
            export_to_excel.setStyleSheet(excel_button_style)
            
            export_layout.addWidget(export_to_pdf)
            export_layout.addSpacing(10)  # Add spacing between buttons
            export_layout.addWidget(export_to_excel)
            export_layout.addStretch()  # Push buttons to the left
            vbox.addLayout(export_layout)

            def export_pdf():
                file_name, _ = QFileDialog.getSaveFileName(
                    preview_dialog,
                    "Export PDF",
                    f"datesheet_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                    "PDF Files (*.pdf)"
                )
                if file_name:
                    generate_pdf(file_name, preview_dialog.metadata, preview_dialog.schedule, preview_dialog.exam_time_range)

            def export_excel():
                file_name, _ = QFileDialog.getSaveFileName(
                    preview_dialog,
                    "Export Excel",
                    f"datesheet_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                    "Excel Files (*.xlsx)"
                )
                if file_name:
                    generate_excel(file_name, preview_dialog.metadata, preview_dialog.schedule, preview_dialog.exam_time_range)

            export_to_pdf.clicked.connect(export_pdf)
            export_to_excel.clicked.connect(export_excel)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(preview_dialog.accept)
            vbox.addWidget(close_btn)
            preview_dialog.exec()

        def on_generate():
            metadata = {
                "college_name": college_name_edit.text(),
                "datesheet_title": title_edit.text(),
                "effective_date": effective_date_edit.text(),
                "department_name": department_edit.text()
            }
            start_date = start_date_edit.date().toString("yyyy-MM-dd")
            exam_start_time = to_24h(exam_start_time_edit)
            exam_end_time = to_24h(exam_end_time_edit)
            selected_days = [cb.text() for cb in day_checks if cb.isChecked()]
            excluded_dates = [d.strip() for d in excluded_dates_edit.text().split(",") if d.strip()]

            if not start_date:
                QMessageBox.warning(dialog, "Missing Data", "Please enter the exam start date.")
                return
            if not exam_start_time or not exam_end_time:
                QMessageBox.warning(dialog, "Missing Data", "Please enter exam start and end times.")
                return
            if not selected_days:
                QMessageBox.warning(dialog, "No Days Selected", "Please select at least one day for exams.")
                return

            entries = collect_entries()
            if not entries:
                QMessageBox.information(dialog, "Info", "Add entries first. These entries will be considered for scheduling.")
                return

            try:
                ga = DatesheetGeneticAlgorithm(
                    entries=entries,
                    max_generations=100,
                    population_size=50,
                    start_date=start_date,
                    exam_start_time=exam_start_time,
                    exam_end_time=exam_end_time,
                    exam_days=selected_days,
                    excluded_dates=excluded_dates
                )
                sched = ga.run()
                if not sched:
                    QMessageBox.information(
                        dialog, "Result",
                        "GA did not produce a schedule.\n\n"
                        "Possible reasons:\n"
                        "- Not enough available days for all exams (check your start date, selected days, and excluded dates)\n"
                        "- Too many exams for the available slots\n"
                        "- Data entry errors (e.g., duplicate courses for a section)\n\n"
                        "Try adjusting your parameters and try again."
                    )
                    return
                show_preview(metadata, sched, exam_start_time, exam_end_time)
                dialog.accept()
            except Exception as ex:
                QMessageBox.critical(dialog, "GA Execution Error", f"Failed to generate datesheet: {ex}")

        generate_btn.clicked.connect(on_generate)
        dialog.exec()

def generate_pdf(file_name, metadata, schedule, exam_time_range):
    doc = QTextDocument()
    
    # HTML content for the PDF, updated to match the reference PDF's style and structure
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header h1 {{
                font-size: 14pt;
                font-weight: bold;
                margin: 0;
            }}
            .header h2 {{
                font-size: 12pt;
                font-weight: normal;
                margin: 5px 0 0;
            }}
            .header p {{
                font-size: 10pt;
                margin: 0;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
            }}
            th, td {{ 
                border: 1px solid black; 
                padding: 8px; 
                text-align: center; 
                vertical-align: top;
            }}
            th {{ 
                background-color: #f0f0f0; 
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{metadata['college_name']}</h1>
            <h2>{metadata['datesheet_title']}</h2>
            <p>Effective Date: {metadata['effective_date']}</p>
            <p>Department: {metadata['department_name']}</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Date & Day</th>
                    <th>Semester/Section</th>
                    <th>Subject (Code)</th>
                    <th>Time</th>
                    <th>Room</th>
                    <th>Invigilator</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Sort exams by date for correct table order
    for exam in sorted(schedule, key=lambda x: x.get('date', '')):
        # Format the 'Date & Day' column
        try:
            date_obj = datetime.strptime(exam.get('date', ''), "%Y-%m-%d")
            date_day_str = f"{date_obj.strftime('%d-%m-%Y')}<br>{date_obj.strftime('%A')}"
        except ValueError:
            date_day_str = f"{exam.get('date', '')}<br>N/A"

        # Format the 'Semester/Section' column
        semester_section_str = f"{exam.get('semester', '')}<br>{exam.get('class_section', '')}"

        # Format the 'Subject (Code)' column
        subject_code_str = f"{exam.get('subject', '')}<br>- {exam.get('course_code', '')}"

        html += f"""
            <tr>
                <td>{date_day_str}</td>
                <td>{semester_section_str}</td>
                <td>{subject_code_str}</td>
                <td>{exam_time_range}</td>
                <td>{exam.get('room', '')}</td>
                <td>{exam.get('teacher', '')}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    doc.setHtml(html)
    printer = QPrinter()
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(file_name)
    doc.print(printer)

def generate_excel(file_name, metadata, schedule, exam_time_range):
    # Create DataFrame
    data = []
    for exam in schedule:
        day_name = datetime.strptime(exam.get('date', ''), "%Y-%m-%d").strftime("%A")
        data.append({
            'Semester': exam.get('semester', ''),
            'Subject': exam.get('subject', ''),
            'Course Code': exam.get('course_code', ''),
            'Class Section': exam.get('class_section', ''),
            'Day': day_name,
            'Date': exam.get('date', ''),
            'Time': exam_time_range,
            'Room': exam.get('room', ''),
            'Shift': exam.get('shift', ''),
            'Teacher': exam.get('teacher', '')
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel writer object
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        # Write metadata
        metadata_df = pd.DataFrame([
            ['College Name', metadata['college_name']],
            ['Title', metadata['datesheet_title']],
            ['Effective Date', metadata['effective_date']],
            ['Department', metadata['department_name']]
        ])
        metadata_df.to_excel(writer, sheet_name='Datesheet', index=False, header=False, startrow=0)
        
        # Write datesheet data
        df.to_excel(writer, sheet_name='Datesheet', index=False, startrow=6)
        
        # Auto-adjust columns width
        worksheet = writer.sheets['Datesheet']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2