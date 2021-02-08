# Created by matveyev at 19.01.2021,

from PyQt5 import QtCore, QtGui
from copy import deepcopy
import xml.etree.cElementTree as ET

device_headers = ('name', 'active', 'device', 'type', 'module', 'control', 'hostname')
online_headers =     ('name', 'active', 'device', 'comment')

check_column = 1
type_column = 2
device_view_role = QtCore.Qt.UserRole + 1

# ----------------------------------------------------------------------
class Node(object):

    def __init__(self, parent, info=None, parent_info=None, row=-1):

        self.parent = parent

        self.part_of_serial_device = isinstance(parent, SerialDeviceNode)
        self.children = []
        self.headers = []

        if info is not None:
            if isinstance(info, dict):
                self.info = info
            else:
                self.info = deepcopy(info.attrib)
                for child in info:
                    if child.tag not in ['group', 'serial_device', 'single_device']:
                        self.info[child.tag] = child.text
        else:
            self.info = {}

        if self.parent is not None:
            self._parent_active = parent.check_status() != QtCore.Qt.Unchecked
            self.parent.add_child(self, row)
            self.parent_info = parent.info
        else:
            self.parent_info = {}

        if parent_info is not None:
            self.parent_info = parent_info
            self.part_of_serial_device = True

        all_attribs = list(self.info.keys()) + list(self.parent_info.keys())

        for name in device_headers:
            if name in all_attribs:
                self.headers.append(name)

        for name in all_attribs:
            if name not in self.headers:
                self.headers.append(name)

    # ----------------------------------------------------------------------
    def add_child(self, child, row=-1):
        if row == -1:
            self.children.append(child)
        else:
            self.children.insert(row, child)
        child.parent = self

    # ----------------------------------------------------------------------
    def remove_child(self, row):
        del self.children[row]

    # ----------------------------------------------------------------------
    @property
    def row(self):
        if self.parent is None:
            return 0
        return self.parent.children.index(self)

    # ----------------------------------------------------------------------
    @property
    def child_item_count(self):
        if len(self.children):
            return len(self.children[0].headers)
        return len(self.headers)

    # ----------------------------------------------------------------------
    @property
    def child_count(self):
        return len(self.children)

    # ----------------------------------------------------------------------
    def child(self, row):
        try:
            return self.children[row]
        except IndexError:
            return None

    # ----------------------------------------------------------------------
    def data(self, column, role):

        if role >= device_view_role:
            role -= device_view_role
            key = self.headers[column].lower()
        else:
            key = online_headers[column].lower()

        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            if key in self.info:
                return self.info[key]
            elif self.part_of_serial_device:
                if key in self.parent_info:
                    return self.parent_info[key]
            elif key == 'device':
                return self.class_name()
            else:
                return ''

        elif role == QtCore.Qt.FontRole:
            my_font = QtGui.QFont()
            if self.check_status() != QtCore.Qt.Unchecked:
                my_font.setBold(True)
            else:
                my_font.setItalic(True)
            return my_font

        elif role == QtCore.Qt.ForegroundRole:
            if not self.check_status() != QtCore.Qt.Unchecked:
                return QtGui.QColor(QtCore.Qt.gray)
            else:
                return QtCore.QVariant()

        elif role == QtCore.Qt.CheckStateRole:
            if column == check_column:
                return self.check_status()
            else:
                return QtCore.QVariant()

    # ----------------------------------------------------------------------
    def set_data(self, column, data, role):

        data_to_set = None

        if role >= device_view_role:
            role -= device_view_role
            key = self.headers[column].lower()
        else:
            key = online_headers[column].lower()

        if role == QtCore.Qt.EditRole:
            data_to_set = data

        elif role == QtCore.Qt.CheckStateRole:
            if data:
                if self.check_status():
                    data_to_set = 'no'
                else:
                    data_to_set = 'yes'
            else:
                data_to_set = 'no'

            for device in self.children:
                device.parent_deactivated(data_to_set == 'yes')

        if data_to_set is None:
            return False

        if key in self.info:
            self.info[key] = data_to_set
        elif self.part_of_serial_device:
            if key in self.parent_info:
                self.parent_info[key] = data_to_set

        return True

    # ----------------------------------------------------------------------
    def flags(self, column):

        if column == check_column:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable
        elif column == type_column and not isinstance(self, DeviceNode):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    # ----------------------------------------------------------------------
    def is_activated(self):
        if 'active' in self.info:
            return self.info['active'] == 'yes'
        else:
            return False

    # ----------------------------------------------------------------------
    def check_status(self):
        return QtCore.Qt.Checked

    # ----------------------------------------------------------------------
    def parent_deactivated(self, status):
        self._parent_active = status
        for device in self.children:
            device.parent_deactivated(status)

    # ----------------------------------------------------------------------
    def deactivate(self):
        self.info['active'] = 'no'
        for device in self.children:
            device.parent_deactivated(False)

    # ----------------------------------------------------------------------
    def class_name(self):
        return ''

    # ----------------------------------------------------------------------
    def class_type(self):
        return ''

    # ----------------------------------------------------------------------
    def get_my_path(self):
        return self.parent.get_my_path() + '/' + self.data(device_headers.index('name'), QtCore.Qt.DisplayRole)

    # ----------------------------------------------------------------------
    def filter_row(self, search_value):
        for value in self.info.values():
            if search_value in value:
                return True
        if self.part_of_serial_device:
            for value in self.parent_info.values():
                if search_value in value:
                    return True
        return False

    # ----------------------------------------------------------------------
    def accept_paste(self, clipboard):

        def _check_serial_device(info):
            equal = True
            for child in clipboard:
                if child.tag not in ['name', 'device']:
                    if child.tag in info:
                        equal *= child.text == info[child.tag]
                    else:
                        equal = False

            return equal

        def _get_cut_device():
            device = ET.Element('single_device', attrib=clipboard.attrib)
            for child in clipboard:
                if child.tag == 'device':
                    _make_sub_element('device', child.text, device, '')

            return device

        paste_enabled = False
        insert_to_parent = False
        device_to_paste = clipboard
        if clipboard is not None:
            # if we have group to paste
            if clipboard.tag in ['group', 'serial_device']:
                # if the destination is device - we can paste group to the parent, if it is not serial_device
                if isinstance(self, DeviceNode) and not isinstance(self.parent, SerialDeviceNode):
                    paste_enabled = True
                    insert_to_parent = True

                # if the destination is group or configuration - we can paste group to the device
                elif isinstance(self, GroupNode) or isinstance(self, ConfigurationNode):
                    paste_enabled = True

            elif clipboard.tag == 'single_device':
                if isinstance(self, DeviceNode):
                    if isinstance(self.parent, SerialDeviceNode):
                        if _check_serial_device(self.parent_info):
                            paste_enabled = True
                            insert_to_parent = True
                            device_to_paste = _get_cut_device()
                    else:
                        paste_enabled = True
                        insert_to_parent = True

                elif isinstance(self, SerialDeviceNode):
                    if _check_serial_device(self.info):
                        paste_enabled = True
                        device_to_paste = _get_cut_device()
                else:
                    paste_enabled = True

        return paste_enabled, insert_to_parent, device_to_paste

    # ----------------------------------------------------------------------
    def get_converted(self):
        if isinstance(self, SerialDeviceNode):
            new_device = ET.Element('group',
                              attrib={'name': self.info['name'],
                                      'active': self.info['active'],
                                      'comment': self.info['comment']})

            for child in self.children:
                child.get_data_to_copy(new_device)
        else:
            new_device = ET.Element('serial_device',
                                    attrib={'name': self.info['name'],
                                            'active': self.info['active'],
                                            'comment': self.info['comment']})

            for key, value in self.children[0].info.items():
                if key not in ['device', 'name', 'comment', 'active']:
                    _make_sub_element(key, value, new_device, '')

            for child in self.children:
                device = ET.SubElement(new_device, 'single_device',
                                       attrib={'name': child.info['name'],
                                               'active': child.info['active'],
                                               'comment': child.info['comment']})
                _make_sub_element('device', child.info['device'], device, '')

        return new_device

    # ----------------------------------------------------------------------
    def can_be_converted(self):
        can_be_converted, caption = False, ''

        if isinstance(self, SerialDeviceNode):
            can_be_converted, caption = True, 'Convert to group'
        elif isinstance(self, GroupNode):
            can_be_converted = True
            caption = 'Convert to serial device'
            if isinstance(self.children[0], DeviceNode):
                properties = dict(self.children[0].info)
                for key in ['device', 'name', 'comment', 'active']:
                    del properties[key]
                for child in self.children[1:]:
                    if isinstance(child, DeviceNode):
                        for key, value in properties.items():
                            if key in child.info:
                                can_be_converted *= value == child.info[key]
                            else:
                                can_be_converted = False
                    else:
                        can_be_converted = False
            else:
                can_be_converted = False

        return can_be_converted, caption

    # ----------------------------------------------------------------------
    def _get_device(self, parent):
        if parent is None:
            return ET.Element(self.class_type().lower(),
                              attrib={'name': self.info['name'],
                                      'active': self.info['active'],
                                      'comment': self.info['comment']})
        else:
            return ET.SubElement(parent, self.class_type().lower(),
                                 attrib={'name': self.info['name'],
                                         'active': self.info['active'],
                                         'comment': self.info['comment']})

    # ----------------------------------------------------------------------
    def get_data_to_copy(self, parent=None):
        me = self._get_device(parent)
        for name, value in self.info.items():
            _make_sub_element(name, value, me, '')

        if isinstance(self, DeviceNode) and self.part_of_serial_device:
            for name, value in self.parent_info.items():
                _make_sub_element(name, value, me, '')
        else:
            for child in self.children:
                child.get_data_to_save(me, '')

        return me

    # ----------------------------------------------------------------------
    def get_data_to_save(self, parent_device=None, depth=''):
        property_element = None
        new_device = self._get_device(parent_device)
        new_device.text = '\n' + depth + '\t'

        for name, value in self.info.items():
            property_element = _make_sub_element(name, value, new_device, depth)

        device = None
        for child in self.children:
            device = child.get_data_to_save(new_device, depth + '\t')

        if device is not None:
            device.tail = '\n' + depth
        elif property_element is not None:
            property_element.tail = '\n' + depth

        new_device.tail = '\n' + depth

        return new_device

    # ----------------------------------------------------------------------
    def get_data_to_export(self):

        new_device = ET.Element('device')
        new_device.text = "\n\t"
        property_element = ET.SubElement(new_device, 'name')
        property_element.text = self.info['name']
        property_element.tail = "\n\t"

        for name, value in self.info.items():
            property_element = _make_sub_element(name, value, new_device)

        if self.part_of_serial_device:
            for name, value in self.parent_info.items():
                property_element = _make_sub_element(name, value, new_device)

        if property_element is not None:
            property_element.tail = '\n'

        new_device.tail = '\n'

        return new_device

# ----------------------------------------------------------------------
class DeviceNode(Node):

    # ----------------------------------------------------------------------
    def check_status(self):
        if self.is_activated() and self._parent_active:
            return QtCore.Qt.Checked
        else:
            return QtCore.Qt.Unchecked

    # ----------------------------------------------------------------------
    def header_data(self):
        return self.headers

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'single_device'

    # ----------------------------------------------------------------------
    def export_devices(self, dev_list):
        if self.check_status() == QtCore.Qt.Checked:
            dev_list.append(self)

# ----------------------------------------------------------------------
class GroupNode(Node):

    # ----------------------------------------------------------------------
    def header_data(self):
        return device_headers[:3]

    # ----------------------------------------------------------------------
    def class_name(self):
        return 'Group'

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'group'

    # ----------------------------------------------------------------------
    def check_status(self):
        if not self.is_activated() or not self._parent_active:
            return QtCore.Qt.Unchecked
        else:
            all_active = True
            for device in self.children:
                all_active *= device.check_status() == QtCore.Qt.Checked
            if all_active:
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.PartiallyChecked

    # ----------------------------------------------------------------------
    def export_devices(self, dev_list):
        for children in self.children:
            children.export_devices(dev_list)

# ----------------------------------------------------------------------
class SerialDeviceNode(GroupNode):

    def header_data(self):
        if len(self.children):
            return self.children[0].header_data()
        else:
            return device_headers[:3]

    # ----------------------------------------------------------------------
    def class_name(self):
        return 'Serial device'

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'serial_device'

# ----------------------------------------------------------------------
class ConfigurationNode(GroupNode):

    # ----------------------------------------------------------------------
    def get_my_path(self):
        return self.info['name']

    # ----------------------------------------------------------------------
    def class_name(self):
        return 'Configuration'

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'configuration'

    # ----------------------------------------------------------------------
    def get_all_activated_devices(self):
        dev_list = []
        for child in self.children:
            child.export_devices(dev_list)

        return dev_list

# ----------------------------------------------------------------------
class OnlineModel(QtCore.QAbstractItemModel):

    def __init__(self, root=None):
        if root is None:
            root = Node(None, None, None)
        self.root = root
        self.root_index = QtCore.QModelIndex()
        super(OnlineModel, self).__init__()

    # ----------------------------------------------------------------------
    def clear(self):
        if len(self.root.children):
            self.beginRemoveRows(self.root_index, 0, len(self.root.children)-1)
            for row in range(len(self.root.children)):
                self.removeRow(self.root.row, self.root_index)
            self.endRemoveRows()

    # ----------------------------------------------------------------------
    def rowCount(self, parent=None, *args, **kwargs):
        node = self.get_node(parent)
        return node.child_count

    # ----------------------------------------------------------------------
    def columnCount(self, parent=None, *args, **kwargs):
        return len(online_headers)

    # ----------------------------------------------------------------------
    def index(self, row, column, parent=None, *args, **kwargs):
        node = self.get_node(parent)
        return self.createIndex(row, column, node.child(row))

    # ----------------------------------------------------------------------
    def parent(self, index=None):
        node = self.get_node(index)
        if node.parent is None:
            return QtCore.QModelIndex()
        return self.createIndex(node.parent.row, 0, node.parent)

    # ----------------------------------------------------------------------
    def data(self, index, role=QtCore.Qt.DisplayRole):
        node = self.get_node(index)
        return node.data(index.column(), role)

    # ----------------------------------------------------------------------
    def setData(self, index, value, role):
        node = self.get_node(index)
        if role in [QtCore.Qt.EditRole, QtCore.Qt.CheckStateRole]:
            if node.set_data(index.column(), value, role):
                self.dataChanged.emit(index, index)
                return True
        return False

    # ----------------------------------------------------------------------
    def flags(self, index):
        node = self.get_node(index)
        return node.flags(index.column())

    # ----------------------------------------------------------------------
    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return online_headers[section]
        return super(OnlineModel, self).headerData(section, orientation, role)

    # ----------------------------------------------------------------------
    def get_node(self, index):
        if index and index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self.root

    # ----------------------------------------------------------------------
    def is_single_device(self, index):
        node = self.get_node(index)
        return isinstance(node, DeviceNode) and not isinstance(node.parent, SerialDeviceNode)

    # ----------------------------------------------------------------------
    def is_serial_device(self, index):
        node = self.get_node(index)
        return isinstance(node, SerialDeviceNode)

    # ----------------------------------------------------------------------
    def is_part_or_serial_device(self, index):
        node = self.get_node(index)
        return isinstance(node.parent, SerialDeviceNode)

    # ----------------------------------------------------------------------
    def removeRow(self, row, parent):
        if not parent.isValid():
            parent_node = self.root
        else:
            parent_node = parent.internalPointer()

        parent_node.remove_child(row)
        return True

    # ----------------------------------------------------------------------
    def remove(self, index):
        node = self.get_node(index)
        self.beginRemoveRows(index.parent(), node.row, node.row)
        self.removeRow(node.row, index.parent())
        self.endRemoveRows()

    # ----------------------------------------------------------------------
    def start_insert_row(self, insert_index, selected_index):
        if selected_index == insert_index:
            row = 0
        else:
            row = self.get_node(selected_index).row
        self.beginInsertRows(insert_index, row, row)
        return self.get_node(insert_index), row

    # ----------------------------------------------------------------------
    def start_adding_row(self, num_elements):
        self.beginInsertRows(self.root_index, 0, num_elements-1)

    # ----------------------------------------------------------------------
    def finish_row_changes(self):
        self.endInsertRows()

    # ----------------------------------------------------------------------
    def filter_row(self, index, value_to_look):
        node = self.get_node(index)
        return node.filter_row(value_to_look)

# ----------------------------------------------------------------------
class DeviceModel(OnlineModel):

    def __init__(self):
        self._last_num_column = 0
        super(DeviceModel, self).__init__()

    # ----------------------------------------------------------------------
    def data(self, index, role=QtCore.Qt.DisplayRole):
        node = self.get_node(index)
        return node.data(index.column(), role+device_view_role)

    # ----------------------------------------------------------------------
    def setData(self, index, value, role):
        node = self.get_node(index)
        if role in [QtCore.Qt.EditRole, QtCore.Qt.CheckStateRole]:
            if node.set_data(index.column(), value, role+device_view_role):
                self.dataChanged.emit(index, index)
                return True
        return False

    # ----------------------------------------------------------------------
    def columnCount(self, parent=None, *args, **kwargs):
        return self.root.child_item_count

    # ----------------------------------------------------------------------
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            header_list = self.root.child(0).header_data()
            if header_list and 0 <= section < len(header_list):
                return header_list[section]
            return None
        else:
            return super(DeviceModel, self).headerData(section, orientation, role)

    # ----------------------------------------------------------------------
    def add_columns(self):
        num_columns = self.root.child_item_count

        if num_columns > self._last_num_column:
            self.beginInsertColumns(self.root_index, self._last_num_column, num_columns - 1)
            self.endInsertColumns()
        elif num_columns < self._last_num_column:
            self.beginRemoveRows(self.root_index, num_columns, self._last_num_column - 1)
            self.endRemoveColumns()

        self._last_num_column = num_columns

# ----------------------------------------------------------------------
class ProxyDeviceModel(QtCore.QSortFilterProxyModel):

    new_version = True

    # ----------------------------------------------------------------------
    def filterAcceptsRow(self, source_row, source_parent):
        if self.new_version:
            return super(ProxyDeviceModel, self).filterAcceptsRow(source_row, source_parent)
        else:
            match = False
            my_index = self.sourceModel().index(source_row, 0, source_parent)
            for row in range(self.sourceModel().rowCount(my_index)):
                match |= self.filterAcceptsRow(row, my_index)

            match |= super(ProxyDeviceModel, self).filterAcceptsRow(source_row, source_parent)

            return match


    # ----------------------------------------------------------------------
    def get_configs_indexes(self):
        indexes = []
        for row in range(self.sourceModel().rowCount(self.sourceModel().root_index)):
            indexes.append(self.mapFromSource(self.sourceModel().index(row, 0, self.sourceModel().root_index)))

        return indexes

# ----------------------------------------------------------------------
def _make_sub_element(name, value, parent, depth=''):
    property_element = None
    if name not in ['active', 'name', 'comment']:
        property_element = ET.SubElement(parent, name)
        property_element.text = value
        property_element.tail = "\n" + depth + "\t"
    return property_element