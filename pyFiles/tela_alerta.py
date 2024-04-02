from kivymd.uix.screen import MDScreen

user_adm_logado = None

# CLASSE DA TELA ALERTA
class TelaAlerta(MDScreen):
    switch_1 = False
    switch_2 = False
    switch_3 = False
    switch_4 = False
    # FUNÇÕES DOS SWITCHS DA TELA ALERTA
    def option_1(self):
        self.switch_1 = not self.switch_1
        if self.switch_1:
            print("Ok")
        else:
            print("Not")

    def option_2(self):
        self.switch_2 = not self.switch_2
        if self.switch_2:
            print("Ok")
        else:
            print("Not")

    def option_3(self):
        self.switch_3 = not self.switch_3
        if self.switch_3:
            print("Ok")
        else:
            print("Not")

    def option_4(self):
        self.switch_4 = not self.switch_4
        if self.switch_4:
            print("Ok")
        else:
            print("Not")