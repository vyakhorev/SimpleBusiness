# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import datetime
import simple_locale
import db_main
import convert

from ui.ui_Dialog_EditPrice import Ui_Dialog_EditClientPrice
from gui_forms_logic.misc import qtdate_pack, qtdate_unpack
from gui_forms_logic.data_models import cDataModel_GeneralMaterialList, cDataModel_PaymentTermsList, cDataModel_CounterpartySpecialList

class gui_Dialog_EditPrice(QtGui.QDialog, Ui_Dialog_EditClientPrice):

    def __init__(self, parent=None):
        super(gui_Dialog_EditPrice, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_price_entity = None
        #Так подтягиваем данные
        self.general_materials_model = cDataModel_GeneralMaterialList(do_load = 0)
        self.payterm_model = cDataModel_PaymentTermsList()
        self.client_model = cDataModel_CounterpartySpecialList(agent_discriminator='client', do_load = 0)
        self.comboBox_SupPrForWichClient.setModel(self.client_model)
        #TODO: фильтровать условия платежа
        self.comboBox_payment_terms.setModel(self.payterm_model)
        self.comboBox_material.setModel(self.general_materials_model)
        self.var_is_correct = False
        self.my_mode = 0   #1 - edit, 0 - new
        self.dateEdit_PriceValidFrom.setMinimumDate(qtdate_pack(datetime.date.today()))
        self.dateEdit_PriceValidTill.setMinimumDate(qtdate_pack(datetime.date.today()))
        self.connect(self.checkBox_is_for_group, QtCore.SIGNAL("stateChanged(int)"), self.update_materials_combobox)
        self.connect(self.comboBox_payment_terms, QtCore.SIGNAL("currentIndexChanged(int)"), self.update_ccy_label)
        self.connect(self.comboBox_material, QtCore.SIGNAL("currentIndexChanged(int)"), self.update_unit_label)
        self.connect(self.checkBox_SupPrIsForSpecClient, QtCore.SIGNAL("stateChanged(int)"), self.resort_clients)
        self.connect(self.checkBox_IsValidBetweenDates, QtCore.SIGNAL("stateChanged(int)"), self.update_valid_between)
        self.connect(self.checkBox_SpecialCond, QtCore.SIGNAL("stateChanged(int)"), self.update_sp_cond_chbox)
        self.connect(self.comboBox_material, QtCore.SIGNAL("currentIndexChanged(int)"), self.resort_clients)
        self.connect(self.checkBox_ClPrPerOrderOnly, QtCore.SIGNAL("stateChanged(int)"), self.update_only_per_order_chbox)
        self.connect(self.checkBox_ClPrIsShipmentTo, QtCore.SIGNAL("stateChanged(int)"), self.update_shipment_to_chbox)
        self.pushButton_LimitToWeek.clicked.connect(self.set_within_week)
        self.pushButton_LimitToMonth.clicked.connect(self.set_within_month)
        self.pushButton_LimitToQuater.clicked.connect(self.set_within_quater)

    def set_state_to_add_new(self, agent_model):
        #Вызываю перед открытием
        self.my_mode = 0
        self.agent_model = agent_model
        self.setWindowTitle(unicode(u"Добавление цены для ") + unicode(self.agent_model.name))
        if self.agent_model.discriminator == 'client':
            self._turn_to_client_mode()
        elif self.agent_model.discriminator == 'supplier':
            self._turn_to_supplier_mode()
        else:
            raise BaseException("Wrong agent type")
        self.__when_open()

    def set_state_to_edit(self, price_entity):
        #Вызываю перед открытием
        self.my_mode = 1
        self.my_price_entity = price_entity
        if price_entity.discriminator == "sell_price":
            self.agent_model = price_entity.client_model
            self._turn_to_client_mode()
        elif price_entity.discriminator == "buy_price":
            self.agent_model = price_entity.supplier_model
            self._turn_to_supplier_mode()
        else:
            raise BaseException("Wrong price type")
        self.setWindowTitle(unicode(u"Изменение цены для ") + unicode(self.agent_model.name))
        self.__when_open()

    def _turn_to_client_mode(self):
        self.groupBox_SupplierPriceDetails.setVisible(False)
        self.groupBox_ClientPriceDetails.setVisible(True)
        self.checkBox_IsFactoring.setVisible(True)
        new_h = 400 - self.groupBox_SupplierPriceDetails.height()
        self.resize(self.width(), new_h)
        self.my_obj_mode = 'client'

    def _turn_to_supplier_mode(self):
        self.groupBox_SupplierPriceDetails.setVisible(True)
        self.groupBox_ClientPriceDetails.setVisible(False)
        self.checkBox_IsFactoring.setVisible(False)
        new_h = 400 - self.groupBox_ClientPriceDetails.height()
        self.resize(self.width(), new_h)
        self.my_obj_mode = 'supplier'

    def __when_open(self):
        if self.my_mode == 1: # Edit
            pr = self.my_price_entity
            self.lineEdit_price.setText(simple_locale.number2string(pr.price_value))
            #Находим индекс элемента (чтобы в комбобоксе то что надо выбрать).
            # 40 - роль для поиска по ключу, ключ - строка, уникальная глобально - string_key()
            #(имя таблицы в базе данных + rec_id записи)
            indx = self.comboBox_payment_terms.findData(pr.payterm.string_key(),40)
            self.comboBox_payment_terms.setCurrentIndex(indx)
            if pr.is_for_group:
                self.checkBox_is_for_group.setCheckState(QtCore.Qt.Checked)
                #Грузим группы материалов в комбобокс
                self.general_materials_model.switch_to_material_types()
                indx = self.comboBox_material.findData(pr.material_type.string_key(),40)
            else:
                self.checkBox_is_for_group.setCheckState(QtCore.Qt.Unchecked)
                #Грузим все номенклатуры в комбобокс
                self.general_materials_model.switch_to_materials()
                indx = self.comboBox_material.findData(pr.material.string_key(),40)
            self.comboBox_material.setCurrentIndex(indx)
            if pr.nonformal_conditions is None: pr.nonformal_conditions = ""
            if pr.nonformal_conditions <> "":
                self.checkBox_SpecialCond.setCheckState(QtCore.Qt.Checked)
                self.update_sp_cond_chbox()
                self.plainTextEdit_special_conditions.setPlainText(pr.nonformal_conditions)
            else:
                self.checkBox_SpecialCond.setCheckState(QtCore.Qt.Unchecked)
                self.update_sp_cond_chbox()
                self.plainTextEdit_special_conditions.setPlainText(u"")
            self.label_currency_name.setText(str(pr.payterm.ccy_quote))
            # Новые фишки
            if pr.min_order_quantity is not None:
                self.lineEdit_ClPrMinOQ.setText(str(pr.min_order_quantity))
            else:
                self.lineEdit_ClPrMinOQ.setText("0")
            if pr.min_order_sum is not None:
                self.lineEdit_ClPrMinOS.setText(str(pr.min_order_sum))
            else:
                self.lineEdit_ClPrMinOS.setText("0")
            if pr.is_valid_between_dates:
                # Это повлечет вызов события
                self.checkBox_IsValidBetweenDates.setCheckState(QtCore.Qt.Checked)
                self.update_valid_between()
                self.dateEdit_PriceValidFrom.setDate(qtdate_pack(pr.date_valid_from))
                self.dateEdit_PriceValidTill.setDate(qtdate_pack(pr.date_valid_till))
            else:
                self.checkBox_IsValidBetweenDates.setCheckState(QtCore.Qt.Unchecked)
                self.update_valid_between()
                self.dateEdit_PriceValidFrom.setDate(qtdate_pack(datetime.datetime.today()))
                self.dateEdit_PriceValidTill.setDate(qtdate_pack(datetime.datetime.today()))
            # Теперь специфичные для клиента / поставщика
            if self.my_obj_mode == 'client':
                if pr.is_delivery:
                    self.checkBox_ClPrIsShipmentTo.setCheckState(QtCore.Qt.Checked)
                    self.lineEdit_ClPrPlaceOfShipment.setText(pr.delivery_place)
                else:
                    self.checkBox_ClPrIsShipmentTo.setCheckState(QtCore.Qt.Unchecked)
                    self.lineEdit_ClPrPlaceOfShipment.setText(u"")
                if pr.is_per_order_only:
                    self.checkBox_ClPrPerOrderOnly.setCheckState(QtCore.Qt.Checked)
                else:
                    self.checkBox_ClPrPerOrderOnly.setCheckState(QtCore.Qt.Unchecked)
                self.update_shipment_to_chbox()
                self.lineEdit_ClPrOrderFulfilmentTerm.setText(str(pr.order_fulfilment_timedelta))
                if pr.is_factoring:
                    self.checkBox_IsFactoring.setCheckState(QtCore.Qt.Checked)
                else:
                    self.checkBox_IsFactoring.setCheckState(QtCore.Qt.Unchecked)
            elif self.my_obj_mode == 'supplier':
                self.lineEdit_SupPrIncotermsPlace.setText(pr.incoterms_place)
                if pr.is_only_for_sp_client:
                    self.checkBox_SupPrIsForSpecClient.setCheckState(QtCore.Qt.Checked)
                    self.resort_clients()
                else:
                    self.checkBox_SupPrIsForSpecClient.setCheckState(QtCore.Qt.Unchecked)
                self.lineEdit_LeadTime.setText(str(pr.lead_time))
        elif self.my_mode == 0: # New
            self.comboBox_payment_terms.setCurrentIndex(-1)
            self.lineEdit_price.setText("")
            self.label_currency_name.setText("")
            self.label_currency_name_2.setText("")
            self.label_units.setText("")
            self.label_units_2.setText("")
            self.checkBox_is_for_group.setCheckState(QtCore.Qt.Checked)
            self.update_materials_combobox()
            self.checkBox_IsFactoring.setCheckState(QtCore.Qt.Unchecked)
            self.lineEdit_ClPrMinOQ.setText("0")
            self.lineEdit_ClPrMinOS.setText("0")
            self.checkBox_IsValidBetweenDates.setCheckState(QtCore.Qt.Checked)
            self.update_valid_between()
            d1 = datetime.date.today()
            d2 = d1 + datetime.timedelta(days=180)
            self.dateEdit_PriceValidFrom.setDate(qtdate_pack(d1))
            self.dateEdit_PriceValidTill.setDate(qtdate_pack(d2))
            if self.my_obj_mode == 'client':
                self.checkBox_ClPrPerOrderOnly.setCheckState(QtCore.Qt.Checked)
                self.update_only_per_order_chbox()
                self.checkBox_ClPrIsShipmentTo.setCheckState(QtCore.Qt.Unchecked)
                self.update_shipment_to_chbox()
                self.lineEdit_ClPrPlaceOfShipment.setText("")
            elif self.my_obj_mode == 'supplier':
                self.lineEdit_SupPrIncotermsPlace.setText("EXW " + self.agent_model.name)
                self.lineEdit_LeadTime.setText(str(5))
                self.checkBox_SupPrIsForSpecClient.setCheckState(QtCore.Qt.Unchecked)
                self.resort_clients()
            self.plainTextEdit_special_conditions.setPlainText(u"")
            self.checkBox_SpecialCond.setCheckState(QtCore.Qt.Unchecked)
            self.update_sp_cond_chbox()


    def update_valid_between(self):
        if self.checkBox_IsValidBetweenDates.checkState() == QtCore.Qt.Checked:
            self.dateEdit_PriceValidFrom.setVisible(True)
            self.dateEdit_PriceValidTill.setVisible(True)
            self.dateEdit_PriceValidFrom.setEnabled(True)
            self.dateEdit_PriceValidTill.setEnabled(True)
            self.pushButton_LimitToWeek.setEnabled(True)
            self.pushButton_LimitToMonth.setEnabled(True)
            self.pushButton_LimitToQuater.setEnabled(True)
            self.pushButton_LimitToWeek.setVisible(True)
            self.pushButton_LimitToMonth.setVisible(True)
            self.pushButton_LimitToQuater.setVisible(True)
        else:
            self.dateEdit_PriceValidFrom.setVisible(False)
            self.dateEdit_PriceValidTill.setVisible(False)
            self.dateEdit_PriceValidFrom.setEnabled(False)
            self.dateEdit_PriceValidTill.setEnabled(False)
            self.pushButton_LimitToWeek.setEnabled(False)
            self.pushButton_LimitToMonth.setEnabled(False)
            self.pushButton_LimitToQuater.setEnabled(False)
            self.pushButton_LimitToWeek.setVisible(False)
            self.pushButton_LimitToMonth.setVisible(False)
            self.pushButton_LimitToQuater.setVisible(False)

    def set_within_week(self):
        d1 = datetime.date.today()
        d2 = d1 + datetime.timedelta(days = 7)
        self.set_between_dates(d1,d2)

    def set_within_month(self):
        d1 = datetime.date.today()
        d2 = d1 + datetime.timedelta(days = 30)
        self.set_between_dates(d1,d2)

    def set_within_quater(self):
        d1 = datetime.date.today()
        d2 = d1 + datetime.timedelta(days = 90)
        self.set_between_dates(d1,d2)

    def set_between_dates(self, d1, d2):
        self.dateEdit_PriceValidFrom.setDate(qtdate_pack(d1))
        self.dateEdit_PriceValidTill.setDate(qtdate_pack(d2))

    def update_sp_cond_chbox(self):
        if self.checkBox_SpecialCond.checkState() == QtCore.Qt.Checked:
            self.plainTextEdit_special_conditions.setEnabled(True)
            self.plainTextEdit_special_conditions.setVisible(True)
        else:
            self.plainTextEdit_special_conditions.setEnabled(False)
            self.plainTextEdit_special_conditions.setVisible(False)

    def update_only_per_order_chbox(self):
        if self.checkBox_ClPrPerOrderOnly.checkState() == QtCore.Qt.Checked:
            self.lineEdit_ClPrOrderFulfilmentTerm.setText(str(60))
        else:
            self.lineEdit_ClPrOrderFulfilmentTerm.setText(str(5))

    def update_shipment_to_chbox(self):
        if self.checkBox_ClPrIsShipmentTo.checkState() == QtCore.Qt.Checked:
            self.lineEdit_ClPrPlaceOfShipment.setVisible(True)
            self.lineEdit_ClPrPlaceOfShipment.setEnabled(True)
        else:
            self.lineEdit_ClPrPlaceOfShipment.setVisible(False)
            self.lineEdit_ClPrPlaceOfShipment.setEnabled(False)

    def update_materials_combobox(self):
        if self.checkBox_is_for_group.checkState() == QtCore.Qt.Checked:
            #Грузим группы материалов в комбобокс
            self.general_materials_model.switch_to_material_types()
        else: #self.checkBox_is_for_group.checkState() == QtCore.Qt.Unchecked:
            #Грузим все номенклатуры в комбобокс
            self.general_materials_model.switch_to_materials()
        self.comboBox_material.setCurrentIndex(-1)

    def resort_clients(self):
        if self.my_obj_mode == 'supplier': # В ином случае вызова не будет
            if self.checkBox_SupPrIsForSpecClient.isChecked():
                self.comboBox_SupPrForWichClient.setEnabled(True)
                self.comboBox_SupPrForWichClient.setVisible(True)
                tp = self.general_materials_model.check_type()
                if tp == 'materials':
                    mat_type = self.get_material().material_type
                elif tp == 'groups':
                    mat_type = self.get_material()
                self.client_model.update_list()
                self.client_model.set_matgr_for_sorting(mat_type)
            else:
                self.comboBox_SupPrForWichClient.setCurrentIndex(-1)
                self.comboBox_SupPrForWichClient.setEnabled(False)
                self.comboBox_SupPrForWichClient.setVisible(False)

    def update_ccy_label(self, i):
        # 35 - наша роль для передачи данных
        payterm = self.comboBox_payment_terms.itemData(i, 35).toPyObject()
        if payterm is not None:
            self.label_currency_name.setText(unicode(payterm.ccy_quote))
            self.label_currency_name_2.setText(unicode(payterm.ccy_quote))
            if payterm.ccy_quote <> payterm.ccy_pay:
                ccy = u"%s (у.е.)"%(payterm.ccy_quote)
                if payterm.fixation_at_shipment:
                    ccy += u" фиксация при отгрузке"
                else:
                    ccy += u" курс по оплате"
            else:
                ccy = u"%s"%(payterm.ccy_quote)
            prepaym = ""
            for t, p in payterm.payterm_stages.get_prepayments():
                if t < 0:
                    prepaym += u"аванс %d%%; "%(int(p))
                elif t == 0:
                    prepaym += u"предоплата %d%%; "%(int(p))
            postpaym = ""
            for t, p in payterm.payterm_stages.get_postpayments():
                prepaym += u"оплата %d%% через %d дней; "%(int(p), int(t))
            desc = u"Расчеты в %s; %s %s"%(ccy, prepaym, postpaym)
            self.label_PayTermDescription.setText(desc)

    def update_unit_label(self, i):
        # 35 - наша роль для передачи данных
        an_item = self.comboBox_material.itemData(i, 35).toPyObject()
        if an_item is not None:
            self.label_units.setText(an_item.measure_unit)
            self.label_units_2.setText(an_item.measure_unit)

    def get_material(self):
        row = self.comboBox_material.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_material.itemData(row, 35).toPyObject()
            return selected_item

    def get_paycond(self):
        row = self.comboBox_payment_terms.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_payment_terms.itemData(row, 35).toPyObject()
            return selected_item

    def get_price_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_price.text())
        except ValueError:
            a_title = unicode(u"Ошибка ввода")
            a_message = unicode(u"Неверно указана цена")
            QtGui.QMessageBox.information(self,a_title,a_message)
            self.var_is_correct = False
            return None

    def get_is_factoring(self):
        if self.checkBox_IsFactoring.checkState() == QtCore.Qt.Checked:
            # Проверим, подходят ли условия платежа
            paycond = self.get_paycond()
            if paycond.fixation_at_shipment:
                # Todo: проверка на валюту - рубли (надо где-то такой объект сделать - основная валюта)
                return True
            else:
                a_title = unicode(u"Ошибка ввода")
                a_message = unicode(u"Условия оплаты не подходят для факторинга")
                QtGui.QMessageBox.information(self,a_title,a_message)
                self.var_is_correct = False
                return None
        else:
            return False

    def get_MOQ(self):
        try:
            if self.lineEdit_ClPrMinOQ.text() == "":
                return 0
            else:
                return convert.convert_formated_str_2_float(self.lineEdit_ClPrMinOQ.text())
        except ValueError:
            return None

    def get_MOS(self):
        try:
            if self.lineEdit_ClPrMinOQ.text() == "":
                return 0
            else:
                return convert.convert_formated_str_2_float(self.lineEdit_ClPrMinOS.text())
        except ValueError:
            return None

    def get_valid_from_date(self):
        return qtdate_unpack(self.dateEdit_PriceValidFrom.date())

    def get_valid_till_date(self):
        return qtdate_unpack(self.dateEdit_PriceValidTill.date())

    def get_order_fulfilment_timedelta(self):
        try:
            td = int(convert.convert_formated_str_2_float(self.lineEdit_ClPrOrderFulfilmentTerm.text()))
            if td>0:
                return td
            else:
                return None
        except ValueError:
            return None

    def get_lead_time(self):
        try:
            td = int(convert.convert_formated_str_2_float(self.lineEdit_LeadTime.text()))
            if td>0:
                return td
            else:
                return None
        except ValueError:
            return None

    def get_the_special_client(self):
        row = self.comboBox_SupPrForWichClient.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_SupPrForWichClient.itemData(row, 35).toPyObject()
            return selected_item

    def inp_erh(self,inp,a_message):
        if inp is None:
            QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Неверно указана графа: ") + a_message)
            self.var_is_correct = False
            return None
        else:
            return inp

    def accept(self):
        # Хорошая идея - создавать dummy переменную для заполнения формы, а потом просто с неё слизывать.
        # Ну или ORM как-то иначе настроить.
        #Перегрузка стандартного метода - читай QDialog
        self.var_is_correct = True
        #Пробегаемся по комбобоксам - проверка заполненности
        if self.var_is_correct:
            general_material = self.inp_erh(self.get_material(),unicode(u"материал"))
            if self.checkBox_is_for_group.checkState() == QtCore.Qt.Checked:
                is_for_group = True
                material_type = general_material
            elif self.checkBox_is_for_group.checkState() == QtCore.Qt.Unchecked:
                is_for_group = False
                material = general_material
        if self.var_is_correct:
            payterm = self.inp_erh(self.get_paycond(),unicode(u"условия платежа"))
        if self.var_is_correct:
            price_value = self.get_price_value()
        if self.var_is_correct:
            MOQ = self.inp_erh(self.get_MOQ(),unicode(u"MOQ (мин. объем заказа)"))
        if self.var_is_correct:
            MOS = self.inp_erh(self.get_MOS(),unicode(u"MOS (мин. стоимость заказа)"))
        if self.checkBox_IsValidBetweenDates.checkState() == QtCore.Qt.Checked:
            is_valid_between_dates = True
            date_valid_from = self.get_valid_from_date()
            date_valid_till = self.get_valid_till_date()
        else:
            is_valid_between_dates = False
        if self.my_obj_mode == 'client': #Это только для цены клиента
            if self.var_is_correct: #Важно, что после get_paycond - надо убедиться, что выбраны
                is_factoring = self.get_is_factoring()
            if self.checkBox_ClPrPerOrderOnly.checkState() == QtCore.Qt.Checked:
                is_per_order_only = True
            else:
                is_per_order_only = False
            if self.checkBox_ClPrIsShipmentTo.checkState() == QtCore.Qt.Checked:
                is_delivery = True
                delivery_place = unicode(self.lineEdit_ClPrPlaceOfShipment.text())
            else:
                is_delivery = False
            order_fulfilment_timedelta = self.inp_erh(self.get_order_fulfilment_timedelta(), unicode(u"срок отгрузки"))
        elif self.my_obj_mode == 'supplier':
            incoterms_place = unicode(self.lineEdit_SupPrIncotermsPlace.text())
            lead_time = self.inp_erh(self.get_lead_time(),unicode(u"lead time"))
            if self.checkBox_SupPrIsForSpecClient.checkState() == QtCore.Qt.Checked:
                is_only_for_sp_client = True
                for_client = self.inp_erh(self.get_the_special_client(),unicode(u"клиент"))
            else:
                is_only_for_sp_client = False
        else:
            raise BaseException(self.my_obj_mode + " - not expected here")
        if self.var_is_correct:
            if self.checkBox_SpecialCond.checkState() == QtCore.Qt.Checked:
                special_cond = unicode(self.plainTextEdit_special_conditions.toPlainText())
            else:
                special_cond = ""
        if self.var_is_correct:
            #Собираем переменную только когда убедились, что всё "ок"
            if self.my_mode == 0: #добавляем новую
                if self.agent_model.discriminator == "client":
                    self.my_price_entity = db_main.c_sell_price()
                    self.my_price_entity.client_model = self.agent_model
                elif self.agent_model.discriminator == "supplier":
                    self.my_price_entity = db_main.c_buy_price()
                    self.my_price_entity.supplier_model = self.agent_model
            self.my_price_entity.is_for_group = is_for_group
            if is_for_group:
                self.my_price_entity.material_type = material_type
                self.my_price_entity.material = None
            else:
                self.my_price_entity.material_type = None
                self.my_price_entity.material = material
            self.my_price_entity.payterm = payterm
            self.my_price_entity.price_value = price_value
            self.my_price_entity.min_order_quantity = MOQ
            self.my_price_entity.min_order_sum = MOS
            self.my_price_entity.is_valid_between_dates = is_valid_between_dates
            if is_valid_between_dates:
                self.my_price_entity.date_valid_from = date_valid_from
                self.my_price_entity.date_valid_till = date_valid_till
            else:
                self.my_price_entity.date_valid_from = None
                self.my_price_entity.date_valid_till = None
            if self.my_price_entity.discriminator == "sell_price":
                self.my_price_entity.is_factoring = is_factoring
                self.my_price_entity.is_per_order_only = is_per_order_only
                self.my_price_entity.is_delivery = is_delivery
                if is_delivery:
                    self.my_price_entity.delivery_place = delivery_place
                else:
                    self.my_price_entity.delivery_place = u""
                self.my_price_entity.order_fulfilment_timedelta = order_fulfilment_timedelta
            elif self.my_price_entity.discriminator == "buy_price":
                self.my_price_entity.incoterms_place = incoterms_place
                self.my_price_entity.lead_time = lead_time
                self.my_price_entity.is_only_for_sp_client = is_only_for_sp_client
                if is_only_for_sp_client:
                    self.my_price_entity.for_client = for_client
                else:
                    self.my_price_entity.for_client = None
            else:
                raise BaseException(self.my_price_entity.discriminator + " - not expected here")
            self.my_price_entity.nonformal_conditions = special_cond
            super(gui_Dialog_EditPrice, self).accept()

    def reject(self):
        #Перегрузка стандартного метода - читай QDialog
        if self.my_mode == 0: #if new, not from database
            self.my_price_entity = None
        super(gui_Dialog_EditPrice, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_price_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]