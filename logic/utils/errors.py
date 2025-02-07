
class InvalidProgramAddress(TypeError):

    def __init__(self, message):
        super().__init__(message)
        self.code = 400


class InvalidProgramSyntax(SyntaxError):

    def __init__(self, message):
        super().__init__(message)
        self.code = 400


class ProgramStateNotSupported(NotImplementedError):

    def __init__(self, message):
        super().__init__(message)
        self.code = 415