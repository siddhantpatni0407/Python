import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
from phonenumbers.phonenumberutil import NumberParseException
from colorama import Fore, Style, init
import pyperclip

init(autoreset=True)

def get_number_info(number):
    try:
        parsed_number = phonenumbers.parse(number)

        # Check validity
        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_possible = phonenumbers.is_possible_number(parsed_number)
        location = geocoder.description_for_number(parsed_number, "en")
        sim_carrier = carrier.name_for_number(parsed_number, "en")
        time_zones = timezone.time_zones_for_number(parsed_number)
        int_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        nat_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        num_type = number_type(parsed_number)

        # Detect type as string
        type_str = {
            PhoneNumberType.MOBILE: "Mobile",
            PhoneNumberType.FIXED_LINE: "Fixed Line",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            PhoneNumberType.TOLL_FREE: "Toll Free",
            PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            PhoneNumberType.VOIP: "VoIP",
            PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
            PhoneNumberType.PAGER: "Pager",
            PhoneNumberType.UAN: "UAN",
            PhoneNumberType.VOICEMAIL: "Voicemail",
            PhoneNumberType.UNKNOWN: "Unknown"
        }.get(num_type, "Unknown")

        # Output
        print(Fore.CYAN + "\n📱 Phone Number Info")
        print(Fore.YELLOW + f"• Entered: {number}")
        print(f"• International Format: {int_format}")
        print(f"• National Format: {nat_format}")
        print(f"• Location: {location}")
        print(f"• Carrier: {sim_carrier}")
        print(f"• Time Zone(s): {', '.join(time_zones)}")
        print(f"• Type: {type_str}")
        print(f"• Valid: {'✅ Yes' if is_valid else '❌ No'}")
        print(f"• Possible: {'✅ Yes' if is_possible else '❌ No'}")

        # Optional: copy to clipboard
        pyperclip.copy(int_format)
        print(Fore.MAGENTA + "📋 International format copied to clipboard!")

    except NumberParseException as e:
        print(Fore.RED + f"\n❌ Error: {e}")

# Loop for multiple lookups
while True:
    number_input = input(Fore.CYAN + "\nEnter mobile number with country code (or 'exit'): ")
    if number_input.lower() in ['exit', 'quit']:
        print(Fore.YELLOW + "👋 Exiting lookup tool.")
        break
    get_number_info(number_input)
