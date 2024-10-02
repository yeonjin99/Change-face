from tkinter import ttk, filedialog
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import os
from reface import syn
import sqlite3
from datetime import datetime
from tkinter import messagebox

class CaptureScreen:
    def __init__(self, master, show_main_screen_callback, db_connection, email_entry, name_entry):
        self.master = master
        self.show_main_screen_callback = show_main_screen_callback
        self.next_window = None
        self.selected_image_path = None
        self.db_connection = db_connection # 데이터베이스 연결
        self.email_entry = email_entry
        self.name_entry = name_entry

        master.title("촬영 화면")

        # OpenCV의 얼굴 인식용 분류기 로드
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # 웹캠 열기
        self.cap = cv2.VideoCapture(0)

        # 전체 화면 크기로 설정
        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.geometry(f"{width}x{height}+0+0")

        # 프레임 추가
        self.frame = tk.Frame(master)
        self.frame.pack(expand=True, fill='both', padx=20, pady=20)

        # 웹캠 화면을 위한 프레임
        self.webcam_frame = tk.Frame(self.frame)
        self.webcam_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # 버튼 프레임 추가
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # 촬영하기 및 취소 버튼 추가
        self.capture_button = tk.Button(self.button_frame, text="촬영하기", command=self.capture, font=("Helvetica", 25))
        self.capture_button.pack(side=tk.LEFT, padx=(50, 20), pady=(0, 100))

        self.cancel_button = tk.Button(self.button_frame, text="취소", command=self.cancel_capture,
                                       font=("Helvetica", 25))
        self.cancel_button.pack(side=tk.LEFT, padx=(30, 0), pady=(0, 100))

        self.capturing = True  # 촬영 중인지 여부를 나타내는 플래그

        # OpenCV에서 웹캠 읽기 시작
        self.show_frame()

    def show_frame(self):
        ret, frame = self.cap.read()

        if ret:
            # 흑백 변환
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 얼굴 찾기
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # 얼굴 주변에 사각형 그리기
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # 촬영 중일 때만 화면에 표시
            if self.capturing:
                frame = cv2.resize(frame, (1000, 750))

                # OpenCV 프레임을 Tkinter PhotoImage로 변환
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR에서 RGB로 변환
                image = Image.fromarray(rgb_frame)
                image = ImageTk.PhotoImage(image)

                # 화면에 표시
                if not hasattr(self, 'label'):
                    self.label = tk.Label(self.webcam_frame, image=image)
                    self.label.image = image
                    self.label.pack(expand=True, fill='both')  # 가운데에 배치
                else:
                    self.label.configure(image=image)
                    self.label.image = image

            # 10ms마다 프레임 갱신
            if self.capturing:
                self.master.after(10, self.show_frame)
            else:
                # 촬영 중이 아니라면, 다른 화면으로 전환
                self.show_main_screen_callback()

    def capture(self):
        # 현재 프레임을 이미지로 저장
        ret, frame = self.cap.read()

        if ret:
            filename = "captured_image.jpg"

            # BGR에서 RGB로 변환하여 저장
            cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            print(f"Image saved as {filename}")

            # 첫 번째 화면으로 돌아가기
            self.show_next_screen()

            # 촬영 중단
            self.capturing = False

            # 선택된 이미지 경로 설정
            self.selected_image_path = filename  # 새로운 코드

            # 웹캠 해제 및 창 닫기
            self.release_capture()
            cv2.destroyAllWindows()

            # 촬영이 완료되면 촬영 화면 창 닫기
            self.master.destroy()

    def show_next_screen(self):
        # Capture 화면 닫기
        self.master.destroy()

        # Capture 화면 표시
        top_level = tk.Toplevel()
        self.next_window = top_level
        self.next_window.title("옵션 선택")

        # 전체 화면으로 크기 조절
        width = self.next_window.winfo_screenwidth()
        height = self.next_window.winfo_screenheight()
        self.next_window.geometry(f"{width}x{height}+0+0")

        # "옵션선택" 제목 라벨 추가
        title_label = tk.Label(self.next_window, text="옵션선택", font=("Helvetica", 30))
        title_label.grid(row=0, column=0, pady=70)  # grid로 변경

        # 라디오 버튼을 표시할 프레임 추가
        radio_frame = tk.Frame(self.next_window)
        radio_frame.grid(row=1, column=0, padx=20, pady=20)  # grid로 변경

        # 라디오 버튼 생성
        choices = ["athlete_woman.jpg", "doctor_woman.jpg", "teacher_woman.jpg", "scientist_woman.jpg", "engineer_woman.jpg", "chef_woman.jpg",
                   "athlete_man.jpg", "doctor_man.jpg", "teacher_man.jpg", "scientist_man.jpg", "engineer_man.jpg", "cooker_man.jpg"]

        selected_image = tk.StringVar(value=choices[0])

        row, col, max_cols = 0, 0, 6  # 초기값 설정

        for choice in choices:
            image_path = os.path.join("photo", choice)
            try:
                # Pillow를 사용하여 이미지 로드
                pil_image = Image.open(image_path)

                # 이미지 크기 조절 (비율 유지)
                pil_image.thumbnail((250, 300))

                image = ImageTk.PhotoImage(pil_image)
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                continue

            # 이미지를 Label에 표시
            radio_button = ttk.Radiobutton(radio_frame, text="", image=image, compound=tk.LEFT,
                                           variable=selected_image, value=choice)
            radio_button.image = image  # 이미지를 가비지 컬렉션에서 보호
            radio_button.grid(row=row, column=col, padx=10, pady=10)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # [선택하기] 버튼 추가
        select_button = tk.Button(self.next_window, text="선택하기",
                                  command=lambda: self.select_image(selected_image.get()),
                                  font=("Helvetica", 20))
        select_button.grid(row=row, column=col, padx=(0, 0), pady=70)  # 5px 왼쪽으로 이동

        # [재촬영하기] 버튼 추가
        recapture_button = tk.Button(self.next_window, text="재촬영하기", command=self.show_capture_screen,
                                     font=("Helvetica", 20))
        recapture_button.grid(row=row, column=col, padx=(350, 0), pady=70)  # 오른쪽에 위치

        # 창 닫기 이벤트 핸들러 등록
        self.next_window.protocol("WM_DELETE_WINDOW", self.on_next_window_close)


    def on_next_window_close(self):
        # Toplevel 창이 닫힐 때에 대한 처리
        if self.next_window and self.next_window.winfo_exists():
            self.next_window.destroy()  # Toplevel 창을 파괴
        if self.master and self.master.winfo_exists():
            self.master.destroy()  # 메인 창을 파괴

    # [선택하기] 버튼 누를 때 옵션 선택 창 닫기
    def select_image(self, selected_image):
        print(f"Selected Image: {selected_image}")
       
        selected_image = "photo/" + str(selected_image)

        # reface.py 모듈의 syn 함수를 사용하여 얼굴 교체 수행
        result_image_path = syn(selected_image)

        # 결과 화면을 표시합니다
        self.show_result_screen(result_image_path)

        # 옵션 선택 창 닫기
        self.next_window.destroy()

    def show_result_screen(self, result_image_path):
        # 결과 화면으로 이동
        result_window = tk.Toplevel()
        result_window.title("합성 결과")

        # ResultScreen 클래스 호출
        result_screen = ResultScreen(result_window, show_main_screen_callback=self.show_main_screen_callback, db_connection=self.db_connection, email_entry=self.email_entry, name_entry=self.name_entry)

        # 창 닫기 이벤트 핸들러 등록
        result_window.protocol("WM_DELETE_WINDOW", self.on_result_window_close)
        result_window.deiconify()  # 창을 표시합니다.

    def on_result_window_close(self):
        # Toplevel 창이 닫힐 때에 대한 처리
        if self.master and self.master.winfo_exists():
            self.master.destroy()  # 메인 창을 파괴

        if root and root.winfo_exists():
            root.destroy()
            root.quit()

            root.quit()

    def cancel_capture(self):
        # 촬영 중단
        self.capturing = False

        # 웹캠 해제 및 창 닫기
        self.cap.release()
        cv2.destroyAllWindows()

        # 현재 창 닫기
        self.master.destroy()

        # 메인 화면 표시
        self.show_main_screen_callback()

    def show_capture_screen(self):
        # 촬영 화면으로 이동
        self.next_window.destroy()  # 이전 창 닫기
        new_capture_window = tk.Toplevel()
        new_capture_window.title("촬영 화면")

        # CaptureScreen 클래스 호출
        new_capture_screen = CaptureScreen(new_capture_window, self.show_main_screen_callback, db_connection=self.db_connection, email_entry=self.email_entry, name_entry=self.name_entry)

        # 창 닫기 이벤트 핸들러 등록
        new_capture_window.protocol("WM_DELETE_WINDOW", new_capture_screen.on_capture_window_close)

    def on_capture_window_close(self):
        # 촬영 중단
        self.capturing = False

        # 웹캠 해제 및 창 닫기
        self.cap.release()
        cv2.destroyAllWindows()

        # 현재 창 닫기
        self.master.destroy()

        # 메인 화면 표시
        self.show_main_screen_callback()

    def release_capture(self):
        # 인스턴스가 파괴될 때 웹캠 리소스 해제
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

class ResultScreen:
    def __init__(self, master, show_main_screen_callback, db_connection, email_entry, name_entry):
        self.master = master
        self.show_main_screen_callback = show_main_screen_callback
        self.result_image_path = None
        self.show_capture_screen = None
        self.db_connection = db_connection # 데이터베이스 연결
        self.email_entry = email_entry
        self.name_entry = name_entry

        master.title("합성 결과")

        # 전체 화면으로 크기 조절
        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.geometry(f"{width}x{height}+0+0")

        # 이미지를 보여줄 라벨 추가
        result_label = tk.Label(master, text="합성 결과", font=("Helvetica", 30))
        result_label.pack(pady=20)

        # 선택된 이미지를 표시하기 위한 라벨
        # Pillow를 사용하여 이미지 로드
        image = Image.open("output.jpg")
        # 이미지 크기 조절 (비율 유지)
        image.thumbnail((900, 900))

        # 이미지 라벨을 프레임으로 감싸기
        image_frame = tk.Frame(master)
        image_frame.pack(expand=True, fill='both', padx=20, pady=(0, 75))  # pady 수정

        image = ImageTk.PhotoImage(image)
        image_label = tk.Label(image_frame, image=image)
        image_label.image = image
        image_label.pack(expand=True, fill='both')  # 이미지를 중앙에 배치

        # 수평 정 가운데에 버튼 배치할 프레임 추가
        button_frame = tk.Frame(master)
        button_frame.pack(pady=(0, 150))

        # [저장하기] 버튼 추가
        save_button = tk.Button(button_frame, text="저장하기", command=self.save_result, font=("Helvetica", 18))
        save_button.pack(side=tk.LEFT, padx=10, pady=10)

        # [다른 옵션 선택] 버튼 추가
        recapture_button = tk.Button(button_frame, text="다른 옵션 선택", command=self.reselect, font=("Helvetica", 18))
        recapture_button.pack(side=tk.LEFT, padx=10, pady=10)

        # [처음으로] 버튼 추가
        restart_button = tk.Button(button_frame, text="처음으로", command=self.on_restart_button_click,
                                   font=("Helvetica", 18))
        restart_button.pack(side=tk.LEFT, padx=10, pady=10)

        # 창 닫기 이벤트 핸들러 등록
        master.protocol("WM_DELETE_WINDOW", self.on_result_window_close)

    def save_result(self):
        # 결과 이미지를 저장할 디렉토리 경로
        save_directory = f"C:/Users/SSVT/Desktop/imagefile/{datetime.now().date()}"

        # 디렉토리가 없으면 생성
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        file_name = datetime.now().strftime("%Y%m%d_%H%M%S")+"_"+self.name_entry.get()+".jpg"

        # 결과 이미지를 선택한 경로에 저장
        self.result_image_path = os.path.join(save_directory, file_name)

        # PIL을 사용하여 이미지 저장
        result_image_pil = Image.fromarray(cv2.cvtColor(cv2.imread("output.jpg"), cv2.COLOR_BGR2RGB))
        result_image_pil.save(self.result_image_path, "JPEG")

        print(f"결과 이미지가 {self.result_image_path}에 저장되었습니다.")

        # 사용자 정보 및 합성 이미지 경로를 데이터베이스에 저장
        if self.result_image_path and self.email_entry.get() and self.name_entry.get():
            # 결과 이미지를 선택한 경로에 저장
            user_email = self.email_entry.get()
            user_name = self.name_entry.get()
            composite_image_path = self.result_image_path


            try:
                cursor = self.db_connection.cursor()
                cursor.execute("INSERT INTO user_data (email, name, composite_image_path) VALUES (?, ?, ?)",
                               (user_email, user_name, composite_image_path))
                self.db_connection.commit()

                # 저장이 완료되면 알림 메시지 표시
                messagebox.showinfo("저장 완료", "결과 이미지가 성공적으로 저장되었습니다.")
            except sqlite3.Error as e:
                print(f"데이터베이스에 데이터를 삽입하는 동안 오류 발생: {e}")
                # 오류 발생 시 에러 메시지를 알림으로 표시
                messagebox.showerror("오류", "저장이 완료되지 않았습니다. 직원에게 문의해주세요.")
            finally:
                cursor.close()
                self.on_restart_button_click()

    def reselect(self):
        # Capture 화면 닫기
        self.master.destroy()

        # Capture 화면 표시
        top_level = tk.Toplevel()
        self.master = top_level
        self.master.title("옵션 선택")

        # 전체 화면으로 크기 조절
        width = self.master.winfo_screenwidth()
        height = self.master.winfo_screenheight()
        self.master.geometry(f"{width}x{height}+0+0")

        # "옵션선택" 제목 라벨 추가
        title_label = tk.Label(self.master, text="옵션선택", font=("Helvetica", 30))
        title_label.grid(row=0, column=0, pady=70)  # grid로 변경

        # 라디오 버튼을 표시할 프레임 추가
        radio_frame = tk.Frame(self.master)
        radio_frame.grid(row=1, column=0, padx=20, pady=20)  # grid로 변경

        # 라디오 버튼 생성
        choices = ["athlete_woman.jpg", "doctor_woman.jpg", "teacher_woman.jpg", "scientist_woman.jpg", "engineer_woman.jpg", "chef_woman.jpg",
                   "athlete_man.jpg", "doctor_man.jpg", "teacher_man.jpg", "scientist_man.jpg", "engineer_man.jpg", "cooker_man.jpg"]

        selected_image = tk.StringVar(value=choices[0])

        row, col, max_cols = 0, 0, 6  # 초기값 설정

        for choice in choices:
            image_path = os.path.join("photo", choice)
            try:
                # Pillow를 사용하여 이미지 로드
                pil_image = Image.open(image_path)

                # 이미지 크기 조절 (비율 유지)
                pil_image.thumbnail((250, 300))

                image = ImageTk.PhotoImage(pil_image)
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                continue

            # 이미지를 Label에 표시
            radio_button = ttk.Radiobutton(radio_frame, text="", image=image, compound=tk.LEFT,
                                           variable=selected_image, value=choice)
            radio_button.image = image  # 이미지를 가비지 컬렉션에서 보호
            radio_button.grid(row=row, column=col, padx=10, pady=10)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1


        # [선택하기] 버튼 추가
        select_button = tk.Button(self.master, text="선택하기",
                                  command=lambda: self.select_image(selected_image.get()),
                                  font=("Helvetica", 20))
        select_button.grid(row=2, column=0, padx=(5, 0), pady=70)  # 5px 왼쪽으로 이동

        # 창 닫기 이벤트 핸들러 등록
        self.master.protocol("WM_DELETE_WINDOW", self.on_next_window_close)

    def on_result_window_close(self):
        # Toplevel 창이 닫힐 때에 대한 처리
        if self.master and self.master.winfo_exists():
            self.master.destroy()  # 합성 결과 창을 파괴

        # 메인 창을 파괴하고 Tkinter의 mainloop를 종료
        if root and root.winfo_exists():
            root.destroy()
            root.quit()

            root.quit()

    def on_next_window_close(self):
        # Toplevel 창이 닫힐 때에 대한 처리
        if self.master and self.master.winfo_exists():
            self.master.destroy()  # 메인 창을 파괴
            if root and root.winfo_exists():
                root.destroy()  # 메인 창을 파괴

                # Tkinter의 mainloop 종료
                root.quit()

    # [선택하기] 버튼 누를 때 옵션 선택 창 닫기
    def select_image(self, selected_image):
        print(f"Selected Image: {selected_image}")
        # 여기서 선택된 이미지에 대한 추가 작업을 수행할 수 있습니다.
        # 예를 들어, 선택된 이미지를 다른 곳에서 사용하거나 특정 동작을 수행할 수 있습니다.
        selected_image = "photo/" + str(selected_image)

        # reface.py 모듈의 syn 함수를 사용하여 얼굴 교체 수행
        result_image_path = syn(selected_image)

        # 결과 화면을 표시합니다
        self.show_result_screen(self.show_main_screen_callback)

        # 옵션 선택 창 닫기
        self.master.destroy()

    def show_result_screen(self, show_main_screen_callback):
        # 결과 화면으로 이동
        result_window = tk.Toplevel()
        result_window.title("합성 결과")

        # ResultScreen 클래스 호출
        result_screen = ResultScreen(result_window, show_main_screen_callback, db_connection=self.db_connection, email_entry=self.email_entry, name_entry=self.name_entry)

        # 창 닫기 이벤트 핸들러 등록
        result_window.protocol("WM_DELETE_WINDOW", self.on_result_window_close)
        result_window.deiconify()  # 창을 표시합니다.

    def on_restart_button_click(self):
        # [처음으로] 버튼을 누를 때 MainGUI 클래스의 시작 화면을 보여주도록 합니다.
        self.master.destroy()

        if self.show_main_screen_callback and callable(self.show_main_screen_callback):
            if self.master and self.master.winfo_exists():
                self.master.destroy()  # 결과 창을 파괴

            self.email_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)

            # 시작 화면을 보여줌
            self.show_main_screen_callback(result_window=self.master)
        else:
            print("show_main_screen_callback is not callable.")

class MainGUI:
    def __init__(self, master, db_connection):
        self.master = master
        self.db_connection = db_connection # 데이터베이스 연결

        master.title("시작 화면")

        # 전체 화면으로 크기 조절
        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.geometry(f"{width}x{height}+0+0")

        # 라벨 추가
        self.label = tk.Label(master, text="FACE CHANGE", font=("Helvetica", 100))
        self.label.place(relx=0.5, rely=0.3, anchor="center")

        # 이메일 입력 필드 추가
        self.email_label = tk.Label(master, text="이메일:", font=("Helvetica", 20))
        self.email_label.place(relx=0.4, rely=0.5, anchor="e")

        self.email_entry = tk.Entry(master, font=("Helvetica", 20))
        self.email_entry.place(relx=0.5, rely=0.5, anchor="w")

        # 이름 입력 필드 추가
        self.name_label = tk.Label(master, text="이름:", font=("Helvetica", 20))
        self.name_label.place(relx=0.4, rely=0.55, anchor="e")

        self.name_entry = tk.Entry(master, font=("Helvetica", 20))
        self.name_entry.place(relx=0.5, rely=0.55, anchor="w")

        # 초기값 설정
        self.email_entry.insert(0, "")
        self.name_entry.insert(0, "")

        # 촬영하기 버튼 추가
        self.capture_button = tk.Button(master, text="촬영하기", command=self.show_capture_screen, font=("Helvetica", 25))
        self.capture_button.place(relx=0.5, rely=0.7, anchor="center")

        # 창 닫기 이벤트 핸들러 등록
        master.protocol("WM_DELETE_WINDOW", self.on_main_window_close)


    def show_capture_screen(self):
        # 이메일 및 이름 가져오기
        user_email = self.email_entry.get()
        user_name = self.name_entry.get()

        # 빈 이메일 또는 이름인 경우 경고 메시지 표시 및 화면 전환 중단
        if not user_email or not user_name:
            messagebox.showwarning("경고", "이메일과 이름을 모두 입력하세요.")
            return

        # 현재 화면 숨기기
        self.master.withdraw()

        # Capture 화면 표시
        capture_window = tk.Toplevel(self.master)
        capture_window.title("촬영화면")

        # CaptureScreen 클래스 호출
        capture_screen = CaptureScreen(capture_window, self.show_main_screen, db_connection=self.db_connection, email_entry=self.email_entry, name_entry=self.name_entry)


        # 창 닫기 이벤트 핸들러 등록
        capture_window.protocol("WM_DELETE_WINDOW", self.on_capture_window_close)
        self.master.wait_window()

    def show_main_screen(self, result_window=None):
        # Capture 화면 닫기
        if result_window and result_window.winfo_exists():
            result_window.destroy()
        self.master.deiconify()
        self.master.update()

    def on_capture_window_close(self):
        # 촬영 화면 창이 닫힐 때 촬영 중단
        self.master.destroy()

    def on_main_window_close(self):
        # 메인 창이 닫힐 때 Tkinter의 mainloop를 종료
        self.master.destroy()
        root.quit()


if __name__ == "__main__":
    # SQLite 데이터베이스에 연결
    db_connection = sqlite3.connect("DBNAME.db")

    # 테이블 생성 쿼리
    create_table_query = '''
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            composite_image_path TEXT
        );
    '''

    # 테이블 생성
    try:
        cursor = db_connection.cursor()
        cursor.execute(create_table_query)
        db_connection.commit()
        print("테이블 생성 또는 이미 존재")
    except sqlite3.Error as e:
        print(f"데이터베이스 테이블 생성 중 오류 발생: {e}")
    finally:
        cursor.close()

    # Tkinter 애플리케이션 시작
    root = tk.Tk()
    app = MainGUI(root, db_connection)
    root.mainloop()

    # 애플리케이션이 종료될 때 데이터베이스 연결 닫기
    db_connection.close()