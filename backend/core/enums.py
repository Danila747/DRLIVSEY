from enum import Enum


class Methods(Enum, tuple):
    ADD_METHODS = ('GET', 'POST',)
    DEL_METHODS = ('DELETE',)
    ACTION_METHODS = tuple(s.lower() for s in (ADD_METHODS + DEL_METHODS))
    UPDATE_METHODS = ('PUT', 'PATCH')
