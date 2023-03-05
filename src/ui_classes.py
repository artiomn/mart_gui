from pathlib import Path
from typing import Optional, List, Union, Any

from PyQt6 import uic, QtCore, QtGui
from PyQt6.QtWidgets import QAbstractItemView, QTableWidget, QWidget, QFileDialog, QMessageBox, QMainWindow, QDialog, \
    QTableWidgetItem, QTextEdit
from PyQt6.QtGui import QColor, QBrush, QTextCursor, QTextCharFormat, QPalette
from PyQt6.QtCore import pyqtSlot, Qt

from markdown_toolset.article_processor import OUT_FORMATS_LIST, IN_FORMATS_LIST
from markdown_toolset.www_tools import is_url
from ordered_set import OrderedSet

from .about_box import AboutBox
from .error_message import ErrorMessage
from .logic import AppLogic
from .resources import res  # noqa
from .item_parameters import ItemParameters
from .log_config import streamer, logging


_logger = logging.getLogger(__name__)


# QtCore.QDir.addSearchPath('icons', (Path(__file__).parent / 'resources' / 'icons').as_posix())

class MainUi(QMainWindow):
    _failed_color = 'darkRed'
    _success_color = 'darkGreen'

    def __init__(self):
        super(MainUi, self).__init__()
        uic.loadUi(Path(__file__).parent / 'resources' / 'mat.ui', self)

        self.btnExit.clicked.connect(self._exit_app)

        self.btnLoadLinks.clicked.connect(self._load_links_file)
        self.btnClearLinks.clicked.connect(self._clear_links)
        self.btnAddLink.clicked.connect(self._add_link)
        self.btnDelLink.clicked.connect(self._del_link)
        self.btnOpenMdFile.clicked.connect(self._open_md_file)

        self.btnStart.clicked.connect(self._start)

        self.btnSelectOutPath.clicked.connect(self._select_download_path_clicked)
        self.btnSelectPubPath.clicked.connect(self._select_image_public_path_clicked)

        self.linksBox.toggled.connect(self._toggled_links_box)
        self.actionLinks_List.triggered.connect(self._toggled_links_box)

        self.viewerBox.toggled.connect(self._toggled_viewer_box)
        self.actionDocument_Editor.triggered.connect(self._toggled_viewer_box)

        self.removeSource.stateChanged.connect(self._toggled_remove_source)
        self.skipIncorrect.stateChanged.connect(self._toggled_skip_incorrect)
        self.downloadIncorrectMIME.stateChanged.connect(self._toggled_download_unrecognized_mime)
        self.saveHierarchy.stateChanged.connect(self._toggled_save_hierarchy)

        self.downloadLinks.setAcceptDrops(True)
        self.downloadLinks.installEventFilter(self)
        self.downloadLinks.viewport().installEventFilter(self)
        self.downloadLinks.cellActivated.connect(self._link_list_cell_activated)
        self.downloadLinks.itemChanged.connect(self._link_list_item_changed)
        self.downloadLinks.currentItemChanged.connect(self._link_list_current_item_changed)
        self.downloadLinks.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.outputPath.setText(Path.cwd().as_posix())
        # self.outputPath.textChanged.connect(self._output_path_changed)
        self.outputPath.editingFinished.connect(self._output_path_changed)
        self.imagesPublicationPath.editingFinished.connect(self._publication_path_changed)
        self.imagesDirectory.editingFinished.connect(self._images_directory_changed)

        self.timeoutSetter.valueChanged.connect(self._timeout_changed)

        self.inputFormatList.addItems([f.upper() for f in IN_FORMATS_LIST])
        self.inputFormatList.currentIndexChanged.connect(self._input_format_changed)

        self.outputFormatList.addItems([f.upper() for f in OUT_FORMATS_LIST])
        self.outputFormatList.currentIndexChanged.connect(self._output_format_changed)

        self.dedupTypeList.addItem(self.tr('Disabled'))
        self.dedupTypeList.addItem(self.tr('By content'))
        self.dedupTypeList.addItem(self.tr('By file name'))
        self.dedupTypeList.currentIndexChanged.connect(self._dedup_type_changed)

        self.skipList.textChanged.connect(self._skip_list_changed)

        self.actionAbout_Qt.triggered.connect(lambda: QMessageBox.aboutQt(self))
        self.actionAbout.triggered.connect(AboutBox)

        self.show()
        self._log('Program started')
        self._app_logic = AppLogic(self._on_complete, self._on_item_success, self._on_item_fail)

    def _log(self, strings: Union[str, List[str]]):
        if isinstance(strings, str):
            _logger.info('%s', strings)
            streamer.seek(0)
            self.logList.addItem(streamer.readline())
            streamer.seek(0)
            streamer.truncate()
        else:
            for s in strings:
                _logger.info('%s', s)
            streamer.seek(0)
            self.logList.addItems(streamer.readlines())
            streamer.seek(0)
            streamer.truncate()

    def _enable_control_box(self):
        enabled = self.downloadLinks.selectionModel().hasSelection()
        self.optionsPage.setEnabled(enabled)
        self.skiplistPage.setEnabled(enabled)

    def _set_link_list_buttons(self):
        select = self.downloadLinks.selectionModel()
        self.btnClearLinks.setEnabled(self.downloadLinks.rowCount() > 0)
        #
        self.btnStart.setEnabled(self.downloadLinks.rowCount() > 0)
        self.btnDelLink.setEnabled(select.hasSelection())
        self.btnOpenMdFile.setEnabled(len(select.selection()) <= 1)

    def _get_links_data(self) -> List[ItemParameters]:
        links_table: QTableWidget = self.downloadLinks

        links = [ld for si in links_table.selectedItems()
                 if (ld := si.data(Qt.ItemDataRole.UserRole)) is not None]

        return links

    def _update_controls(self):
        self._enable_control_box()
        self._set_link_list_buttons()
        self._item_parameters_to_ui(self._get_links_data())

    @staticmethod
    def _set_checkbox_state(checkbox, state: int, no_block=False):
        try:
            if not no_block:
                checkbox.blockSignals(True)

            if state == 0:
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                checkbox.setTristate(False)
                checkbox.setChecked(False)
            elif state == 1:
                checkbox.setTristate(True)
                checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            elif state == 2:
                checkbox.setCheckState(Qt.CheckState.Checked)
                checkbox.setTristate(False)
                checkbox.setChecked(True)
        finally:
            if not no_block:
                checkbox.blockSignals(False)

    @staticmethod
    def _set_control(control, value: Any):
        try:
            control.blockSignals(True)
            control.setValue(value)
        finally:
            control.blockSignals(False)

    @staticmethod
    def _bool_to_tri_state(s: bool) -> int:
        return 2 if s else 0

    @staticmethod
    def _set_default(p: ItemParameters, property_name: str, value):
        if getattr(p, property_name) != value:
            p.set_default(property_name)

    def _item_parameters_to_ui(self, ips: List[ItemParameters]) -> None:
        """
        Translate item parameters to the UI, when string in the items table was selected.

        :param ips: items list.
        """
        p = ItemParameters()
        new_skip_set = OrderedSet()
        skip_set_common: bool = False

        first_item = True

        for i in ips:
            if first_item:
                p.skip_list = sorted(i.skip_list)
                p.downloading_timeout = i.downloading_timeout
                p.output_format = i.output_format
                p.output_path = i.output_path
                p.images_public_path = i.images_public_path
                p.input_format = i.input_format
                p.deduplication_type = i.deduplication_type
                p.images_dir_name = i.images_dir_name

                p.remove_source = self._bool_to_tri_state(i.remove_source)
                p.save_hierarchy = self._bool_to_tri_state(i.save_hierarchy)
                p.download_incorrect_mime = self._bool_to_tri_state(i.download_incorrect_mime)
                p.skip_all_incorrect = self._bool_to_tri_state(i.skip_all_incorrect)
                new_skip_set.update(p.skip_list)
                # List can contains duplicates.
                if list(new_skip_set) != p.skip_list:
                    skip_set_common = True

                first_item = False
                continue

            self._set_default(p, 'remove_source', self._bool_to_tri_state(i.remove_source))
            self._set_default(p, 'save_hierarchy', self._bool_to_tri_state(i.save_hierarchy))
            self._set_default(p, 'download_incorrect_mime', self._bool_to_tri_state(i.download_incorrect_mime))
            self._set_default(p, 'skip_all_incorrect', self._bool_to_tri_state(i.skip_all_incorrect))
            self._set_default(p, 'downloading_timeout', i.downloading_timeout)
            self._set_default(p, 'output_format', i.output_format)
            self._set_default(p, 'input_format', i.input_format)
            self._set_default(p, 'deduplication_type', i.deduplication_type)
            self._set_default(p, 'output_path', i.output_path)
            self._set_default(p, 'images_public_path', i.images_public_path)
            self._set_default(p, 'images_dir_name', i.images_dir_name)

            s_skip_list = sorted(i.skip_list)
            if list(new_skip_set) != s_skip_list:
                new_skip_set.update(s_skip_list)
                skip_set_common = True

        controls = self.controlToolBox.findChildren(QWidget)
        try:
            for c in controls:
                c.blockSignals(True)

            for cb, var in ((self.removeSource, p.remove_source), (self.skipIncorrect, p.skip_all_incorrect),
                            (self.downloadIncorrectMIME, p.download_incorrect_mime),
                            (self.saveHierarchy, p.save_hierarchy)):
                self._set_checkbox_state(cb, var, True)

            self.timeoutSetter.setValue(p.downloading_timeout)
            self.inputFormatList.setCurrentIndex(p.input_format)
            self.outputFormatList.setCurrentIndex(p.output_format)
            self.dedupTypeList.setCurrentIndex(p.deduplication_type)

            if not p.output_path:
                self.outputPath.clear()
            else:
                self.outputPath.setText(p.output_path)
            self.imagesPublicationPath.setText(p.images_public_path)
            self.imagesDirectory.setText(p.images_dir_name)

            if skip_set_common:
                # if I use `self.skipList`, text color is gray.
                self.skipList.setStyleSheet(
                    f'QPlainTextEdit {{color: {self.palette().mid().color().name()};}}')
            else:
                self.skipList.setStyleSheet(
                    f'QPlainTextEdit {{color: {self.palette().text().color().name()};}}')

            self.skipList.setPlainText('\n'.join(new_skip_set))
        finally:
            for c in controls:
                c.blockSignals(False)

    def _file_dialog_setup(self, file_name: str):
        if (p := Path(file_name)).is_dir():
            self._file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        elif p.is_file():
            self._file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

    def _open_file_dialog(self, title: str, root: Optional[Path] = None,
                          without_dir: bool = False, save_state: Optional[bytes] = None,
                          filters: Optional[List[str]] = None):
        dlg = self._file_dialog = QFileDialog()
        # Need to select directory.
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog)

        if not without_dir:
            dlg.setFileMode(QFileDialog.FileMode.Directory)
            dlg.currentChanged.connect(self._file_dialog_setup)

        if root is not None and root:
            if root.is_file():
                root = root.parent
            dlg.setDirectory(root.as_posix())

        dlg.setWindowTitle(title)
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if filters is not None:
            dlg.setNameFilters(filters)

        if dlg.exec():
            if save_state is not None:
                dlg.saveState()

            return dlg.selectedFiles()[0]

    def _get_path(self, control, title):
        if res_path := self._open_file_dialog(title, Path(control.text())):
            control.setText(res_path)

    def eventFilter(self, source, event):
        if source is self.downloadLinks.viewport():
            if event.type() == QtCore.QEvent.Type.DragEnter or event.type() == QtCore.QEvent.Type.DragMove:
                event.accept()
                return True
            elif event.type() == QtCore.QEvent.Type.Drop and event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    if url.isLocalFile():
                        self._load_links(url.path())
                event.accept()
                return True
        return super().eventFilter(source, event)

    @pyqtSlot()
    def _skip_list_changed(self):
        for link_data in self._get_links_data():
            link_data.skip_list = self.skipList.toPlainText().split()
        self.skipList.setStyleSheet(
            f'QPlainTextEdit {{color: {self.palette().text().color().name()};}}')

    @pyqtSlot(int)
    def _input_format_changed(self, index: int):
        for link_data in self._get_links_data():
            link_data.input_format = index

    @pyqtSlot(int)
    def _output_format_changed(self, index: int):
        for link_data in self._get_links_data():
            link_data.output_format = index

    @pyqtSlot(int)
    def _dedup_type_changed(self, index: int):
        for link_data in self._get_links_data():
            link_data.deduplication_type = index

    @pyqtSlot()
    def _output_path_changed(self):
        text = self.outputPath.text()
        for link_data in self._get_links_data():
            link_data.output_path = text

    @pyqtSlot()
    def _publication_path_changed(self):
        text = self.imagesPublicationPath.text()
        for link_data in self._get_links_data():
            link_data.images_public_path = text

    @pyqtSlot()
    def _images_directory_changed(self):
        text = self.imagesDirectory.text()
        for link_data in self._get_links_data():
            link_data.images_dir_name = text

    @pyqtSlot()
    def _select_download_path_clicked(self):
        self._get_path(self.outputPath, self.tr('Select output file or directory'))

    @pyqtSlot()
    def _select_image_public_path_clicked(self):
        self._get_path(self.publicationPath, self.tr('Select public image directory'))

    @pyqtSlot(int, int)
    def _link_list_cell_activated(self, row: int, col: int):
        if row >= 0:
            links_table = self.downloadLinks
            item: ItemParameters = links_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

            if item.downloaded:
                self.documentEditor: QTextEdit
                self.documentEditor.setEnabled(True)
                self.documentEditor.setDocumentTitle(str(item.output_file_path))
                with open(item.output_file_path, 'r') as f:
                    self.documentEditor.setMarkdown(f.read())
            else:
                self.documentEditor.setEnabled(False)
        else:
            self.documentEditor.setEnabled(False)

        self._update_controls()

    @pyqtSlot(QTableWidgetItem)
    def _link_list_item_changed(self, item: QTableWidgetItem):
        self._update_controls()

    @pyqtSlot(QTableWidgetItem, QTableWidgetItem)
    def _link_list_current_item_changed(self, item1: QTableWidgetItem, item2: QTableWidgetItem):
        self._update_controls()
        ld: ItemParameters = getattr(item1, 'linked_data', None)
        if ld is not None:
            out_path = Path(ld.output_path)
            if out_path.exists() and out_path.is_file():
                with open(out_path) as f:
                    self.documentEditor.setMarkdown(f.read())

    @pyqtSlot(int)
    def _toggled_remove_source(self, state: int):
        self.removeSource.setTristate(False)

        for link_data in self._get_links_data():
            link_data.remove_source = bool(state)

    @pyqtSlot(int)
    def _toggled_skip_incorrect(self, state: int):
        self.skipIncorrect.setTristate(False)

        for link_data in self._get_links_data():
            link_data.skip_all_incorrect = bool(state)

    @pyqtSlot(int)
    def _toggled_download_unrecognized_mime(self, state: int):
        self.downloadIncorrectMIME.setTristate(False)

        for link_data in self._get_links_data():
            link_data.download_incorrect_mime = bool(state)

    @pyqtSlot(int)
    def _toggled_save_hierarchy(self, state: int):
        self.saveHierarchy.setTristate(False)

        for link_data in self._get_links_data():
            link_data.save_hierarchy = bool(state)

    @pyqtSlot(int)
    def _timeout_changed(self, value: int):
        for link_data in self._get_links_data():
            link_data.downloading_timeout = value

    @pyqtSlot(bool)
    def _toggled_viewer_box(self, state: bool):
        self.viewerBox.setChecked(state)
        self.actionDocument_Editor.setChecked(state)
        self.leftContainer.setVisible(state)

    @pyqtSlot(bool)
    def _toggled_links_box(self, state: bool):
        self.actionLinks_List.setChecked(state)
        self.linksBox.setChecked(state)
        self.rightContainer.setVisible(state)

    @pyqtSlot()
    def _load_links_file(self):
        if res_path := self._open_file_dialog(self.tr('Open file with links to download'), without_dir=True):
            self._load_links(res_path)

    @staticmethod
    def _hl_item(item: QTableWidgetItem, color: str):
        item.setForeground(QBrush(QColor(color)))

    def _hl_row(self, row_num: int, color: str):
        links_table: QTableWidget = self.downloadLinks
        try:
            links_table.blockSignals(True)
            self._hl_item(links_table.item(row_num, 0), color)
        finally:
            links_table.blockSignals(False)
            links_table.repaint()

    def _hl_failed_row(self, row_num):
        self._hl_row(row_num, self._failed_color)

    def _hl_successful_row(self, row_num: int):
        self._hl_row(row_num, self._success_color)

    def _load_links(self, res_path: Union[Path, str]):
        links_table: QTableWidget = self.downloadLinks

        try:
            links_table.blockSignals(True)

            with open(res_path, 'r') as lf:
                ls = []
                err_log = []

                for line in lf:
                    try:
                        lrs = line.rstrip()

                        if not lrs:
                            continue

                        ls.append(lrs)
                    except UnicodeError as e:
                        err_log.append(str(e))

                if err_log:
                    ErrorMessage(self, '\n'.join(err_log))

                strings = {nl: l for nl, l in enumerate(ls)}
                prev_row_count = links_table.rowCount()
                links_table.setRowCount(prev_row_count + len(strings))

                err_log.clear()

                for nl, line in strings.items():
                    item = QTableWidgetItem(line)
                    try:
                        if not is_url(line) and not Path(line).is_file():
                            self._hl_item(item, self._failed_color)
                        self._add_download_link(prev_row_count + nl, item)
                    except Exception as e:
                        _logger.error('%s', e)
                        err_log.append(str(e))

                if err_log:
                    ErrorMessage(self, '\n'.join(err_log))

            if links_table.rowCount() > 0:
                links_table.selectRow(0)
        except Exception as e:
            ErrorMessage(self, self.tr(f'Can\'t load file "{res_path}": {str(e)}'))
        finally:
            links_table.blockSignals(False)
            self._update_controls()

    @pyqtSlot()
    def _clear_links(self):
        self.downloadLinks.setRowCount(0)
        self._update_controls()

    @pyqtSlot()
    def _add_link(self):
        links_table = self.downloadLinks

        row_number = links_table.rowCount()
        links_table.setRowCount(row_number + 1)
        self._add_download_link(row_number)

    @pyqtSlot()
    def _del_link(self):
        table = self.downloadLinks

        try:
            table.blockSignals(True)
            indexes = table.selectionModel().selectedRows()

            for i in indexes:
                table.removeRow(i.row())

        finally:
            table.blockSignals(False)
            self._update_controls()

    @pyqtSlot()
    def _open_md_file(self):
        filename = self._open_file_dialog(self.tr('Open Markdown article file'), without_dir=True,
                                          filters=[self.tr('Markdown files (*.md)'),
                                                   self.tr('All files (*)')])

        if filename is None:
            return

        links_table = self.downloadLinks

        try:
            links_table.blockSignals(True)
            if 0 == links_table.rowCount():
                links_table.setRowCount(1)
                self._add_download_link(0, QTableWidgetItem(filename))
            else:
                indexes = links_table.selectionModel().selectedRows()

                assert len(indexes) == 1, 'Incorrect selection'
                self._add_download_link(indexes[0].row(), QTableWidgetItem(filename))

        finally:
            links_table.blockSignals(False)
            self._update_controls()

    def _get_download_links(self, row_numbers: List[int]) -> List[QTableWidgetItem]:
        links_table: QTableWidget = self.downloadLinks
        return [links_table.item(rn, 0) for rn in row_numbers]

    def _get_row_by_text(self, text: str) -> int:
        links_table: QTableWidget = self.downloadLinks

        result = links_table.findItems(text, Qt.MatchFlag.MatchExactly)

        if 0 == len(result):
            raise ValueError(f'Cant\'t find text "{text}"')

        return result[0].row()

    def _add_download_link(self, row_number: int, item: Optional[QTableWidgetItem] = None):
        links_table: QTableWidget = self.downloadLinks
        if item is None:
            item = QTableWidgetItem()

        item.setData(Qt.ItemDataRole.UserRole, ItemParameters())
        links_table.setItem(row_number, 0, item)

        if not links_table.selectionModel().selectedRows():
            links_table.selectRow(0)

    @pyqtSlot()
    def _start(self):
        if self._app_logic.running:
            self._log('User stopped work...')
            self._app_logic.stop()
            self.btnStart.setText(self.tr('Start'))
        else:
            self._log('Work started...')
            self.btnStart.setText(self.tr('Stop'))
            links_table = self.downloadLinks

            download_files = [(item.text(), item.row(), item.data(Qt.ItemDataRole.UserRole)) for i
                              in range(links_table.rowCount()) if (item := links_table.item(i, 0))]
            self._app_logic.add_items(download_files)

    def _on_complete(self):
        self._log('Work completed...')
        self.btnStart.setText(self.tr('Start'))

    def _on_item_success(self, index, file_path):
        self._hl_successful_row(index)
        links_table = self.downloadLinks
        item: ItemParameters = links_table.item(index, 0).data(Qt.ItemDataRole.UserRole)
        item.downloaded = True
        item.output_file_path = file_path

    def _on_item_fail(self, index, file_path):
        self._hl_failed_row(index)

    @pyqtSlot()
    def _exit_app(self):
        _logger.debug('Exiting')
        self.close()
