from enum import Enum

# Define an Enum for mapping numerical player count to text used in element IDs
class PlayerCountMap(Enum):
    ONE = "one"
    TWO = "two"
    THREE = "three"
    FOUR = "four"

    @classmethod
    def from_number(cls, number):
        """
        Converts a numerical player count (string or int) to the corresponding Enum member.
        Returns None if no match.
        """
        try:
            num_str = str(number)
            if num_str == "1":
                return cls.ONE
            elif num_str == "2":
                return cls.TWO
            elif num_str == "3":
                return cls.THREE
            elif num_str == "4":
                return cls.FOUR
            else:
                return None
        except (ValueError, TypeError):
            return None

    def to_id_text(self):
        """
        Returns the text representation used in the element ID (e.g., "two").
        """
        return self.value 