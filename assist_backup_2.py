from collections import UserDict
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime, date
import re
import pickle

# Клас Field, який буде батьківським для всіх полів, 
# у ньому потім реалізуємо логіку, загальну для всіх полів.   
class Field:
    def __init__(self, value) -> None:
        self.value = value
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return str(self)

# Клас Name, обов'язкове поле з ім'ям.     
class Name(Field):
    def __init__(self, first_name, last_name=None) -> None:
        if last_name:
            self.value = f"{first_name} {last_name}"
        else:
            self.value = first_name
        # self.value = self.value.replace(" ", "")


# Клас Phone, необов'язкове поле з телефоном 
# та таких один запис (Record) може містити кілька.   
class Phone(Field):

    def __init__(self, value) -> None:
            if not self._is_valid_phone(value):
                raise ValueError("Invalid phone number format. Please enter 10 digits without spaces or separators.")
            self.__value = value

    @staticmethod
    def _is_valid_phone(phone):
        pattern = r'^\d{10}$'
        return bool(re.match(pattern, phone))

    @property
    def value(self):
        return self.__value 
    
    @value.setter
    def value(self, value):
        if not self._is_valid_phone(value):
            raise ValueError("Invalid phone number format. Please enter 10 digits without spaces or separators.")
        self.__value = value

    def __str__(self):
        return self.__value


class BirthdayError(BaseException):
    def __init__(self, message="Invalid birthday date. Please enter date format dd-mm-yyyy") -> None:
        super().__init__(message)



class Birthday(Field):
    def __init__(self, value) -> None:
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        # патерн для коректної роботи зміни дня народження
        pattern = r'^\d{2}-\d{2}-\d{4}$'
        if not re.match(pattern, value):
            raise BirthdayError("Invalid birthday date. Please enter date format dd-mm-yyyy")

        try:
            date_obj = datetime.strptime(value, "%d-%m-%Y")
            self.__value = date_obj
        except ValueError:
            raise BirthdayError("Invalid birthday date. Please enter date format dd-mm-yyyy")

    def __str__(self):
        return self.__value.strftime("%d-%m-%Y")



# Клас Record, який відповідає за логіку додавання/видалення/редагування 
# необов'язкових полів та зберігання обов'язкового поля Name.
# Клас Record приймає ще один додатковий (опціональний) аргумент класу Birthday. Це поле не обов'язкове 
class Record:
    def __init__(self, name: Name, phone: Phone = None, Birthday: Birthday = None) -> None:
        self.name = name
        self.phones = []
        if phone:
            self.phones.append(phone)
        self.birthday = Birthday

    def change_birthday(self, new_birthday: Birthday):
        self.birthday = new_birthday
        return f"Birthday changed to {new_birthday} for contact {self.name}"
    
    def add_phone(self, phone: Phone):
        if phone.value not in [p.value for p in self.phones]:
            self.phones.append(phone)
            return f"phone {phone} add to contact {self.name}"
        return f"{phone} present in phones of contact {self.name}"
    
    def change_phone(self, old_phone, new_phone):
        for idx, p in enumerate(self.phones):
            if old_phone.value == p.value:
                self.phones[idx] = new_phone
                return f"old phone {old_phone} change to {new_phone}"
        return f"{old_phone} not present in phones of contact {self.name}"

    def change_name(self, new_name: Name):
        self.name = new_name
        return f"Name changed to {new_name} for contact {self.name}"    


# Додамо функцію days_to_birthday, яка повертає кількість днів до наступного дня народження.
    def days_to_birthday(self):
        if self.birthday:
            today = date.today()
            birthday_date = self.birthday.value.date()
            birthday_date = birthday_date.replace(year=today.year)

            if birthday_date < today:
                birthday_date = birthday_date.replace(year=today.year + 1)

            days_to_birthday = (birthday_date - today).days
            return days_to_birthday
        return None


    def __str__(self) -> str:
        birthday_info = ""
        if self.birthday:
            days_to_birthday = self.days_to_birthday()
            birthday_info = f", Days to birthday: {days_to_birthday}" if days_to_birthday is not None else ""
        return f"{self.name}: {', '.join(str(p) for p in self.phones)}{birthday_info}"


# Клас AddressBook, який наслідується від UserDict, 
# та ми потім додамо логіку пошуку за записами до цього класу.
class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[str(record.name)] = record
        return f"Contact {record} add success"
    
    def delete_record(self, name: str):
        if name in self.data:
            del self.data[name]
            return f"Contact with name '{name}' deleted successfully"
        return f"No contact with name '{name}' in address book"
    
# метод iterator, який повертає генератор за записами. Пагінація    
    def __iter__(self, n=5):
        keys = list(self.data.keys())
        for i in range(0, len(keys), n):
            chunk = {key: self.data[key] for key in keys[i:i + n]}
            yield chunk
    

    def __str__(self) -> str:
        return "\n".join(str(r) for r in self.data.values())
# another module .py


    def __init__(self):
        super().__init__()
        self.load_from_file()  # завантажує записи під час ініціалізації

    def add_record(self, record: Record):
        self.data[str(record.name)] = record
        self.save_to_file()  # зберегти після додавання
        return f"Contact {record} added successfully"

    def delete_record(self, name: str):
        if name in self.data:
            del self.data[name]
            self.save_to_file()  # зберегти після видалення
            return f"Contact with name '{name}' deleted successfully"
        return f"No contact with name '{name}' in the address book"

    def save_to_file(self):
        with open("adress.bin", "wb") as file:
            pickle.dump(self.data, file)

    def load_from_file(self):
        try:
            with open("adress.bin", "rb") as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            # якщо файл відсутній, створити
            self.data = {}


address_book = AddressBook()


def input_error(func):
    def wrapper(*args):
        try:
            return func(*args)
        except IndexError as e:
            return e
        except NameError as e:
            return e
        except BirthdayError as e:
            return e
        except ValueError as e:
            return e
        except TypeError as e:
            return e
    return wrapper


# Record реалізує методи для додавання об'єктів Phone.
@input_error
def add_command(*args):
    name = args[0]
    last_name = ""
    phone_number = None
    birthday = None

    # При більше ніж одному аргументі, другий це прізвище, третій - телефон
    # четвертий аргумент - день народження
    if len(args) > 1:
        # чи є прийнятним номер телефону
        if len(args[-1]) == 10 and args[-1].isdigit():
            phone_number = Phone(args[-1])
            if len(args) >= 3:
                last_name = args[1]
            if len(args) >= 4:
                birthday = Birthday(args[2])
        else:
            last_name = args[1]
            if len(args) >= 3:
                phone_number = Phone(args[2])
                if len(args) >= 4:
                    birthday = Birthday(args[3])

     # Чи існує контакт
    record_name = f"{name} {last_name}".strip()
    rec = address_book.get(record_name)
    if rec:
        if phone_number:
            return rec.add_phone(phone_number)
        if birthday:
            return rec.change_birthday(birthday)
        return f"Contact {record_name} already exists in the address book."

    # Створюємо name, phone number, and birthday
    name_field = Name(f"{name} {last_name}".strip())
    rec = Record(name_field, phone_number, birthday)
    address_book.save_to_file()
    return address_book.add_record(rec)


@input_error
def change_command(*args):
    name = Name(args[0])
    old_phone = Phone(args[1])
    new_phone = Phone(args[2])
    new_birthday = Birthday(args[3]) if len(args) >= 4 and args[3] else None  # Додали обробку дня народження
    rec: Record = address_book.get(str(name))
    if rec:
        if new_birthday:  # додали зміну дня народження
            rec.birthday = new_birthday
        address_book.save_to_file()
        return rec.change_phone(old_phone, new_phone)
    return f"No contact {name} in address book"


@input_error
def edit_name_command(*args):
    name = Name(args[0])
    new_name = Name(args[1])
    birthday = Birthday(args[2]) if len(args) > 2 else None  # обробка дати народження
    rec: Record = address_book.get(str(name))
    if rec:
        if birthday:  # умова для зміни дня народження
            rec.birthday = birthday
            address_book.save_to_file()
            return f"Birthday changed to {birthday} for contact {rec.name}"
        address_book.save_to_file()
        return rec.change_name(new_name)
    return f"No contact {name} in address book"



# Record реалізує методи для видалення об'єктів Phone.
@input_error
def delete_contact_command(*args):
    if args:
        name = args[0]
        address_book.save_to_file()
        return address_book.delete_record(name)
    else:
        return "Please provide a name to delete the contact."

@input_error
def find_command(*args):
    query = args[0]  # Або номер або ім'я
    
    matching_records = []
    for record in address_book.data.values():
        # Перевірка відповідності запиту імені чи номеру телефону
        if query.lower() in str(record.name).lower() \
                or any(query.lower() in str(phone).lower() for phone in record.phones):
            matching_records.append(record)
    
    if matching_records:
        console = Console()
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name")
        table.add_column("Phone number")

        for record in matching_records:
            name = str(record.name)
            phone_numbers = ', '.join([str(phone) for phone in record.phones])
            table.add_row(name, phone_numbers)

        console.print(table)
    else:
        return f"No records found for the query: {query}"


def exit_command(*args):
    return "Good bye!"
    

def unknown_command(*args):
    pass


def show_all_command(*args):
    if address_book.data:
        console = Console()
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name")
        table.add_column("Phone number")
        table.add_column("Birthday", style="dim")

        for record in address_book.data.values():
            name = str(record.name)
            phone_numbers = ', '.join([str(phone) for phone in record.phones])
            birthday = str(record.birthday) if record.birthday else "N/A"
            table.add_row(name, phone_numbers, birthday)

        console.print(table)
    else:
        print('No contacts saved.')
#     return address_book


def hello_command(*args):
    return "How can I help you?"


def show_address_book():
    if address_book:
        page_number = 1
        for chunk in address_book:
            console = Console()
            table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
            table.add_column("Name")
            table.add_column("Phone number")
            table.add_column("Birthday", style="dim")

            for record in chunk.values():
                name = str(record.name)
                phone_numbers = ', '.join([str(phone) for phone in record.phones])
                birthday = str(record.birthday) if record.birthday else "N/A"
                table.add_row(name, phone_numbers, birthday)

            console.print(f"Page {page_number}:")
            console.print(table)
            page_number += 1
    else:
        print('No contacts saved.')

@input_error
def change_birthday_command(*args):
    name = Name(args[0])
    new_birthday = Birthday(args[1])
    rec = address_book.get(str(name))
    if rec:
        address_book.save_to_file()
        return rec.change_birthday(new_birthday)
    return f"No contact {name} in address book"


COMMANDS = {
    add_command: ("add", "+", "2"),
    change_command: ("change", "зміни", "3"),
    exit_command: ("bye", "exit", "end", "0"),
    delete_contact_command:("del","8"),
    find_command: ("find", "4"),
    show_all_command: ("show all", "5"),
    hello_command:("hello", "1"),
    edit_name_command: ("edit", "7"),
    show_address_book: ("page", "**"),
    change_birthday_command: ("bday", "6")   
}



def parser(text: str):
    for cmd, kwds in COMMANDS.items():
        for kwd in kwds:
            if text.lower().startswith(kwd):
                data = text[len(kwd):].strip().split()
                if cmd in [change_command, edit_name_command]:
                    if len(data) < 3:
                        data.append(None)
                return cmd, data
    return unknown_command, []


def main():
    while True:
        user_input = input("--->>> ")
        
        cmd, data = parser(user_input)

        result = cmd(*data)

        print(result)
        
        if cmd == exit_command:
            break
 

if __name__ == "__main__":
    address_book = AddressBook()
    main()