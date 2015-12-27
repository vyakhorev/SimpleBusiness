# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore

class ui_TagHighlighter(QtGui.QSyntaxHighlighter):
    # Выделяем цветом все ключевые слова (которые хештеги)
    def __init__(self, parent, theme):
        QtGui.QSyntaxHighlighter.__init__( self, parent)
        self.parent = parent
        self.taq_format = QtGui.QTextCharFormat()
        self.highlightingRules = []
        brush = QtGui.QBrush(QtCore.Qt.darkMagenta, QtCore.Qt.SolidPattern)
        self.taq_format.setForeground(brush)
        self.taq_format.setFontWeight(QtGui.QFont.Bold)

    def update_keywords(self, new_keywords_list):
        # TODO: не засорять память, обнуляя каждый раз массив
        keywords = QtCore.QStringList(new_keywords_list)
        for word in keywords:
            pattern = QtCore.QRegExp(word, QtCore.Qt.CaseInsensitive)
            rule = HighlightingRule(pattern, self.taq_format)
            self.highlightingRules += [rule]

    def highlightBlock(self, text):
        #Do the thing!
        for rule in self.highlightingRules:
            expression = QtCore.QRegExp(rule.pattern)
            index = expression.indexIn(text)
            while index >= 0: #... Looks strange
                length = expression.matchedLength()
                self.setFormat(index, length, rule.format)
                index = text.indexOf(expression, index + length)
        self.setCurrentBlockState(0)

class HighlightingRule():
    def __init__( self, pattern, format):
        self.pattern = pattern
        self.format = format






