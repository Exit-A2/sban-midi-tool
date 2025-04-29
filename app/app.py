from PIL import Image
import customtkinter as ctk
import tkinter.filedialog as tkfd


FONT = "meiryo"
WIDTH = 720
HEIGHT = 405


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.title("すべあなMIDIサポーター")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.from_morse_frame = FromMorseFrame(
            master=self, width=WIDTH, height=HEIGHT, fg_color="gray20"
        )

        self.tool_selector = ToolSelector(master=self, width=WIDTH, height=HEIGHT)
        self.tool_selector.grid(row=0, column=0)

        self.change_page(self.tool_selector)

    def change_page(self, page: ctk.CTkFrame):
        self.tool_selector.place_forget()
        page.grid(row=0, column=0)


class ToolSelector(ctk.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rowconfigure((0, 1), weight=1)
        self.columnconfigure((0, 1, 2), weight=1)

        button1 = self.tool_button(
            "モールスからMIDI",
            "resources/p.png",
            self.master.from_morse_frame,
        )
        button1.grid(row=0, column=0, sticky="nsew")

        button2 = self.tool_button(
            "点字からMIDI",
            "resources/p.png",
            self.master.from_morse_frame,
        )
        button2.grid(row=0, column=1, sticky="nsew")

    def tool_button(self, text, image, page):
        return ctk.CTkButton(
            master=self,
            text=text,
            font=(FONT, 15),
            image=ctk.CTkImage(Image.open(image)),
            compound="top",
            width=80,
            height=80,
            fg_color="gray30",
            hover_color="gray20",
            corner_radius=0,
            command=lambda: self.master.change_page(page),
        )


class MidiSelector(ctk.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rowconfigure(0)
        self.columnconfigure(1, weight=1)

        self.button_select = ctk.CTkButton(
            master=self,
            text="ファイルを選択",
            font=(FONT, 15),
            command=self.select_midi,
        )
        self.button_select.grid(row=0, column=0, padx=(5, 10))

        self.string_path = ctk.StringVar(self, "")

        self.entry_path = ctk.CTkEntry(
            master=self, textvariable=self.string_path, font=(FONT, 15)
        )
        self.entry_path.grid(row=0, column=1, sticky="nsew")

    def select_midi(self):
        path = tkfd.askopenfilename(
            filetypes=[("MIDIファイル", "*.mid"), ("MIDIファイル", "*.midi")]
        )
        self.string_path.set(path)


class LengthSelector(ctk.CTkComboBox):
    def __init__(self, master):
        super().__init__(
            master=master,
            font=(FONT, 15),
            dropdown_font=(FONT, 15),
            values=[
                "全音符",
                "2分音符",
                "4分音符",
                "8分音符",
                "16分音符",
                "32分音符",
                "64分音符",
            ],
        )


class FromMorseFrame(ctk.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        LengthSelector(self).grid()


if __name__ == "__main__":
    app = App()
    app.mainloop()
    print(app.tool_selector)
    print(type(app.tool_selector))
