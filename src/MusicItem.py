from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
)
from ParamDialog import ParamDialog


class MusicItem(QGraphicsRectItem):
    def __init__(self, x, y, width, name="Clip", settings = None, track_height=40):
        width = float(width) if isinstance(width, (int, float)) else float(width[0])
        super().__init__(x, y, width, track_height)
        self.settings = settings  # Salva il riferimento alle settings
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # Abilita la selezione
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.color = QColor(100, 150, 200)  # Default color
        self.setBrush(self.color)
        self.setPen(QPen(Qt.black))
        self.name = name
        self.text = QGraphicsTextItem(self.name, self)
        self.text.setPos(5, track_height/4)
        self.drag_start = None
        self.track_index = 0  # inizializza
        
        self.params = {
            "cAttacco": 0,
            "durataArmonica": 26,
            "ritmo": [7,15],
            "durata": 5,
            "ampiezza": [-30,-0.25],
            "frequenza": [6,1],
            "posizione": -8
        }

    def updateTextStyle(self):
        if self.settings:
            font = self.text.font()
            font.setPointSize(self.settings.get('text_size', 12))
            self.text.setFont(font)
            self.text.setDefaultTextColor(QColor(self.settings.get('text_color', '#000000')))

    def paint(self, painter, option, widget):
            super().paint(painter, option, widget)
            if hasattr(self, 'highlighted') and self.highlighted:
                # Disegna l'evidenziazione della ricerca
                pen = QPen(QColor(255, 165, 0), 3)  # Arancione per l'evidenziazione della ricerca
                painter.setPen(pen)
                painter.drawRect(self.rect())
            elif self.isSelected():
                # Disegna l'evidenziazione della selezione
                pen = QPen(Qt.blue, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.drawRect(self.rect())

    def mouseDoubleClickEvent(self, event):
        self.showParamDialog()

    def showParamDialog(self):
        dialog = ParamDialog(self.params, self.color)
        if dialog.exec_():
            for key, input_field in dialog.inputs.items():
                try:
                    if isinstance(self.params[key], list):
                        from ast import literal_eval
                        value = literal_eval(input_field.text())
                        
                        # Funzione di conversione migliorata
                        def convert_to_float(val):
                            if isinstance(val, (list, tuple)):
                                return [float(x) if isinstance(x, (int, float, str)) else convert_to_float(x) for x in val]
                            return float(val)
                        
                        # Converti il valore mantenendo la struttura originale
                        self.params[key] = convert_to_float(value)
                    else:
                        self.params[key] = float(input_field.text())
                        
                except (ValueError, SyntaxError) as e:
                    print(f"Errore nel parsing del parametro {key}: {e}")
                    continue
            
            self.color = dialog.color
            self.setBrush(self.color)
            
            if self.scene():
                new_x = self.params['cAttacco'] * self.scene().pixels_per_beat * self.scene().zoom_level
                new_width = self.params['durata'] * self.scene().pixels_per_beat * self.scene().zoom_level
                self.setPos(new_x, self.pos().y())
                self.setRect(0, 0, new_width, self.rect().height())
                self.text.setPos(5, self.rect().height()/4)
                    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value
            grid_size = (self.scene().pixels_per_beat * self.scene().zoom_level) / 16
            grid_x = round(newPos.x() / grid_size) * grid_size
            
            track_y = self.scene().grid_height + (max(0, min(
                round((newPos.y() - self.scene().grid_height) / self.scene().track_height),
                self.scene().num_tracks - 1
            )) * self.scene().track_height)
            
            # Update cAttacco
            self.params['cAttacco'] = round(grid_x / (self.scene().pixels_per_beat * self.scene().zoom_level),3)
            
            # Only move other items during direct drag, not during recursive updates
            if self.isSelected() and not hasattr(self, '_updating'):
                original_pos = self.pos()
                delta = QPointF(grid_x - original_pos.x(), track_y - original_pos.y())
                
                self._updating = True  # Prevent recursive updates
                try:
                    for item in self.scene().selectedItems():
                        if item != self and isinstance(item, MusicItem):
                            new_item_pos = item.pos() + delta
                            item.setPos(new_item_pos)
                            item.params['cAttacco'] = new_item_pos.x() / (self.scene().pixels_per_beat * self.scene().zoom_level)
                finally:
                    delattr(self, '_updating')
            
            return QPointF(grid_x, track_y)
            
        return super().itemChange(change, value)


    def mousePressEvent(self, event):
        if event.modifiers() & Qt.MetaModifier:  # Command/Meta key
            self.showParamDialog()
            return 
        self.drag_start = event.scenePos()
        if not event.modifiers() & Qt.ControlModifier:
            if not self.isSelected():
                scene = self.scene()
                if scene:
                    for item in scene.selectedItems():
                        item.setSelected(False)
            self.setSelected(True)
        super().mousePressEvent(event)


    
    def mouseMoveEvent(self, event):
        if self.drag_start:
            delta = event.scenePos() - self.drag_start
            grid_size = (self.scene().pixels_per_beat * self.scene().zoom_level) / 16
            new_x = round((self.pos().x() + delta.x()) / grid_size) * grid_size
            
            track_y = self.scene().grid_height + (max(0, min(
                round((event.scenePos().y() - self.scene().grid_height) / self.scene().track_height),
                self.scene().num_tracks - 1
            )) * self.scene().track_height)
            
            self.setPos(new_x, track_y)
            self.params['cAttacco'] = round(new_x / (self.scene().pixels_per_beat * self.scene().zoom_level),3)
            
            if self.isSelected():
                for item in self.scene().selectedItems():
                    if item != self and isinstance(item, MusicItem):
                        item.setPos(item.pos() + delta)
                        item.params['cAttacco'] = round(item.pos().x() / (self.scene().pixels_per_beat * self.scene().zoom_level),3)
            
            self.drag_start = event.scenePos()
            
    def mouseReleaseEvent(self, event):
        self.drag_start = None
        super().mouseReleaseEvent(event)
        
    
