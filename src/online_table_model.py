# Created by matveyev at 19.01.2021,

from PyQt5 import QtCore, QtGui
import xml.etree.cElementTree as ET

device_headers = ('Name', 'Active', 'Device', 'Type', 'Module', 'Control', 'Hostname')
online_headers = ('Name', 'Active', 'Device', 'Comment')

check_column = 1
type_column = 2
device_view_role = QtCore.Qt.UserRole + 1

# ----------------------------------------------------------------------
class Node(object):

    def __init__(self, parent, main, my_id, info=None, item_count=0):

        self.parent = parent
        self.item_count = item_count
        self.my_id = my_id
        self.info = info
        self.serial_device = None
        self.children = []
        self.main = main

        if self.parent is not None:
            self._parent_active = parent._check_status() != QtCore.Qt.Unchecked
            self.parent.add_child(self)

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
            return self.children[0].item_count
        return self.item_count

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
            if key in self.info.keys():
                return self.info.attrib[key]
            else:
                for child in self.info:
                    if child.tag == key:
                        return child.text
                if self.serial_device is not None:
                    for child in self.serial_device.info:
                        if child.tag == key:
                            return child.text
                if key == 'device':
                    return self.class_type()

                return ''

        elif role == QtCore.Qt.FontRole:
            my_font = QtGui.QFont()
            if self._check_status() != QtCore.Qt.Unchecked:
                my_font.setBold(True)
            else:
                my_font.setItalic(True)
            return my_font

        elif role == QtCore.Qt.ForegroundRole:
            if not self._check_status() != QtCore.Qt.Unchecked:
                return QtGui.QColor(QtCore.Qt.gray)
            else:
                return QtCore.QVariant()

        elif role == QtCore.Qt.CheckStateRole:
            if column == check_column:
                return self._check_status()
            else:
                return QtCore.QVariant()

    # ----------------------------------------------------------------------
    def set_data(self, column, data, role):

        data_to_set = None

        if role >= device_view_role:
            role -= device_view_role
            key = device_headers[column].lower()
        else:
            key = online_headers[column].lower()

        if role == QtCore.Qt.EditRole:
            data_to_set = data

        elif role == QtCore.Qt.CheckStateRole:
            if data:
                if self._check_status():
                    data_to_set = 'no'
                else:
                    data_to_set = 'yes'
            else:
                data_to_set = 'no'

            for device in self.children:
                device._parent_deactivated(data_to_set =='yes')

        if data_to_set is None:
            return False

        if key in self.info.keys():
            self.info.attrib[key] = data_to_set
        else:
            for child in self.info:
                if child.tag == key:
                    child.text = data_to_set
                    break
            if self.serial_device is not None:
                for child in self.serial_device.info:
                    if child.tag == key:
                        child.text = data_to_set
                        break

        self.main.save_library()
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
        if 'active' in self.info.attrib:
            return self.info.attrib['active'] == 'yes'
        else:
            return False

    # ----------------------------------------------------------------------
    def _check_status(self):
        return QtCore.Qt.Checked

    # ----------------------------------------------------------------------
    def _parent_deactivated(self, status):
        self._parent_active = status
        for device in self.children:
            device._parent_deactivated(status)

    # ----------------------------------------------------------------------
    def deactivate(self):
        self.info.attrib['active'] = 'no'
        for device in self.children:
            device._parent_deactivated(False)

    # ----------------------------------------------------------------------
    def class_type(self):
        return ''

    # ----------------------------------------------------------------------
    def get_my_path(self):
        return self.parent.get_my_path() + '/' + self.data(device_headers.index('Name'), QtCore.Qt.DisplayRole)

    # ----------------------------------------------------------------------
    def filter_row(self, search_value):
        if self.info is None:
            return True
        for value in self.info.values():
            if search_value in value:
                return True
        for child in self.info:
            if search_value in child.text:
                return True
        if self.serial_device is not None:
            for child in self.serial_device.info:
                if search_value in child.text:
                    return True
        return False

# ----------------------------------------------------------------------
class DeviceNode(Node):

    def __init__(self, parent, main, my_id, info, serial_device=None):

        if serial_device is not None:
            all_keys = [child.tag for child in info.getchildren() + serial_device.info.getchildren()
                        if child.tag != 'single_device']
        else:
            all_keys = [child.tag for child in info]

        all_keys += info.attrib.keys()
        self.headers = []

        for name in device_headers:
            if name.lower() in all_keys:
                self.headers.append(name.lower())

        for key in all_keys:
            if key not in self.headers:
                self.headers.append(key.lower())

        super(DeviceNode, self).__init__(parent, main, my_id, info, len(self.headers))

        self.serial_device = serial_device

    # ----------------------------------------------------------------------
    def _check_status(self):
        if self.is_activated() and self._parent_active:
            return QtCore.Qt.Checked
        else:
            return QtCore.Qt.Unchecked

    # ----------------------------------------------------------------------
    def header_data(self):
        return self.headers

    # ----------------------------------------------------------------------
    def is_exported(self):
        return self._check_status() == QtCore.Qt.Checked

    # ----------------------------------------------------------------------
    def get_data_to_export(self):
        new_device = ET.Element('device')
        new_device.text = '\n\t'

        all_properties = self.info.getchildren()
        if self.serial_device is not None:
            all_properties += self.serial_device.info.getchildren()

        property_element = ET.SubElement(new_device, 'name')
        property_element.text = self.info.attrib['name']
        property_element.tail = "\n\t"

        for child in all_properties:
            if child.tag != 'single_device':
                property_element = ET.SubElement(new_device, child.tag)
                property_element.text = child.text
                property_element.tail = "\n\t"
        property_element.tail = "\n"

        new_device.tail = '\n'

        return new_device

# ----------------------------------------------------------------------
class GroupNode(Node):

    # ----------------------------------------------------------------------
    def header_data(self):
        return device_headers[:3]

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'Group'

    # ----------------------------------------------------------------------
    def _check_status(self):
        if not self.is_activated() or not self._parent_active:
            return QtCore.Qt.Unchecked
        else:
            all_active = True
            for device in self.children:
                all_active *= device._check_status() == QtCore.Qt.Checked
            if all_active:
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.PartiallyChecked

# ----------------------------------------------------------------------
class SerialDeviceNode(GroupNode):

    def header_data(self):
        if len(self.children):
            return self.children[0].header_data()
        else:
            return device_headers[:3]

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'Serial device'

# ----------------------------------------------------------------------
class ConfigurationNode(GroupNode):

    # ----------------------------------------------------------------------
    def get_my_path(self):
        return self.info.attrib['name']

    # ----------------------------------------------------------------------
    def class_type(self):
        return 'Configuration'

# ----------------------------------------------------------------------
class OnlineModel(QtCore.QAbstractItemModel):

    def __init__(self, root=None):
        if root is None:
            root = Node(None, None, None)
        self.root = root
        super(OnlineModel, self).__init__()

    # ----------------------------------------------------------------------
    def clear(self):
        self.root = Node(None, None, None)

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
            return node.set_data(index.column(), value, role)
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
    def insertRow(self, row, parent, device):
        if not parent.isValid():
            parent_node = self.root
        else:
            parent_node = parent.internalPointer()

        parent_node.add_child(device, row)
        return True

    # ----------------------------------------------------------------------
    def remove(self, index):
        node = self.get_node(index)
        self.beginRemoveRows(index.parent(), node.row, node.row)
        self.removeRow(node.row, index.parent())
        self.endRemoveRows()

    # ----------------------------------------------------------------------
    def start_adding(self, index):
        self.beginInsertRows(index.parent(), self.rowCount(index.parent()), self.rowCount(index.parent()))

    # ----------------------------------------------------------------------
    def finish_adding(self):
        self.endInsertRows()

    # ----------------------------------------------------------------------
    def filter_row(self, index, value_to_look):
        node = self.get_node(index)
        return node.filter_row(value_to_look)

# ----------------------------------------------------------------------
class DeviceModel(OnlineModel):

    def __init__(self):
        self.root_index = QtCore.QModelIndex()
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
            return node.set_data(index.column(), value, role+device_view_role)
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
    def clear(self):
        if len(self.root.children):
            self.beginRemoveRows(self.root_index, 0, len(self.root.children)-1)
            for row in range(len(self.root.children)):
                self.removeRow(self.root.row, self.root_index)
            self.endRemoveRows()

    # ----------------------------------------------------------------------
    def start_adding(self, num_elements):
        self.beginInsertRows(self.root_index, 0, num_elements-1)

    # ----------------------------------------------------------------------
    def finish_adding(self):
        self.endInsertRows()

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
    pass



