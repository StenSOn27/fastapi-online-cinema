from abc import ABC, abstractmethod


class EmailSenderInterface(ABC):

    @abstractmethod
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        """
        Asynchronously send an account activation email.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to include in the email.
        """
        pass
    
    @abstractmethod
    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """
        Asynchronously send an account activation complete email.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass

    @abstractmethod
    async def send_password_reset_email(self, email, reset_link: str) -> None:
        pass
    
    @abstractmethod
    async def send_password_reset_complete_email(self, email, login_link: str) -> None:
        pass
    
    @abstractmethod
    async def send_password_change_complete_email(self, email, login_link: str) -> None:
        pass
    
    @abstractmethod
    async def send_successfull_payment_email(self, email, order_id: int) -> None:
        pass
