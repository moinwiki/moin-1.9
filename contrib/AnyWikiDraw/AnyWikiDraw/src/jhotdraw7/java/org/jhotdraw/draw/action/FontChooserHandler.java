/**
 * @(#)FontChooserHandler.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.draw.action;

import javax.swing.undo.*;
import javax.swing.*;
import java.util.*;
import java.awt.*;
import java.beans.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.gui.JFontChooser;

/**
 * FontChooserHandler.
 *
 * @author Werner Randelshofer
 * @version $Id: FontChooserHandler.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FontChooserHandler extends AbstractSelectedAction
        implements PropertyChangeListener {

    protected AttributeKey<Font> key;
    protected JFontChooser fontChooser;
    protected JPopupMenu popupMenu;
    protected int isUpdating;
    //protected Map<AttributeKey, Object> attributes;

    /** Creates a new instance. */
    public FontChooserHandler(DrawingEditor editor, AttributeKey<Font> key, JFontChooser fontChooser, JPopupMenu popupMenu) {
        super(editor);
        this.key = key;
        this.fontChooser = fontChooser;
        this.popupMenu = popupMenu;

        fontChooser.addActionListener(this);
        fontChooser.addPropertyChangeListener(this);
        updateEnabledState();
    }

    public void actionPerformed(java.awt.event.ActionEvent evt) {
        if (evt.getActionCommand() == JFontChooser.APPROVE_SELECTION) {
            applySelectedFontToFigures();
        } else if (evt.getActionCommand() == JFontChooser.CANCEL_SELECTION) {
        }
        popupMenu.setVisible(false);
    }

    protected void applySelectedFontToFigures() {
        final ArrayList<Figure> selectedFigures = new ArrayList<Figure>(getView().getSelectedFigures());
        final ArrayList<Object> restoreData = new ArrayList<Object>(selectedFigures.size());
        for (Figure figure : selectedFigures) {
            restoreData.add(figure.getAttributesRestoreData());
            key.set(figure, fontChooser.getSelectedFont());
        }
        getEditor().setDefaultAttribute(key, fontChooser.getSelectedFont());
        final Font undoValue = fontChooser.getSelectedFont();
        UndoableEdit edit = new AbstractUndoableEdit() {

            @Override
            public String getPresentationName() {
                return AttributeKeys.FONT_FACE.getPresentationName();
            /*
            String name = (String) getValue(Actions.UNDO_PRESENTATION_NAME_KEY);
            if (name == null) {
            name = (String) getValue(AbstractAction.NAME);
            }
            if (name == null) {
            ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
            name = labels.getString("attribute.text");
            }
            return name;*/
            }

            @Override
            public void undo() {
                super.undo();
                Iterator<Object> iRestore = restoreData.iterator();
                for (Figure figure : selectedFigures) {
                    figure.willChange();
                    figure.restoreAttributesTo(iRestore.next());
                    figure.changed();
                }
            }

            @Override
            public void redo() {
                super.redo();
                for (Figure figure : selectedFigures) {
                    restoreData.add(figure.getAttributesRestoreData());
                    figure.willChange();
                    key.basicSet(figure, undoValue);
                    figure.changed();
                }
            }
        };
        fireUndoableEditHappened(edit);
    }

    @Override
    protected void updateEnabledState() {
        setEnabled(getEditor().isEnabled());
        if (getView() != null && fontChooser != null && popupMenu != null) {
            fontChooser.setEnabled(getView().getSelectionCount() > 0);
            popupMenu.setEnabled(getView().getSelectionCount() > 0);
            isUpdating++;
            if (getView().getSelectionCount() > 0 /*&& fontChooser.isShowing()*/) {
                for (Figure f : getView().getSelectedFigures()) {
                    if (f instanceof TextHolderFigure) {
                        TextHolderFigure thf = (TextHolderFigure) f;
                        fontChooser.setSelectedFont(thf.getFont());
                        break;
                    }
                }
            }
            isUpdating--;
        }
    }

    public void propertyChange(PropertyChangeEvent evt) {
        if (isUpdating++ == 0) {
            if (evt.getPropertyName() == JFontChooser.SELECTED_FONT_PROPERTY) {
                applySelectedFontToFigures();
            }
        }
        isUpdating--;
    }
}
