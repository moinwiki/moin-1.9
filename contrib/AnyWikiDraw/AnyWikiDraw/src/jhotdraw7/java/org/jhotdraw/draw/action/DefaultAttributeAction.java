/*
 * @(#)DefaultAttributeAction.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
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

import org.jhotdraw.undo.*;
import javax.swing.*;
import java.beans.*;
import java.util.*;
import org.jhotdraw.draw.*;

/**
 * DefaultAttributeAction.
 * <p>
 * XXX - should listen to changes in the default attributes of its DrawingEditor.
 *
 * @author  Werner Randelshofer
 * @version $Id: DefaultAttributeAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DefaultAttributeAction extends AbstractSelectedAction {
    private AttributeKey[] keys;
    private Map<AttributeKey,Object> fixedAttributes;
    
    
    /** Creates a new instance. */
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey key) {
        this(editor, key, null, null);
    }
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey key, Map<AttributeKey,Object> fixedAttributes) {
        this(editor, new AttributeKey[] { key }, null, null, fixedAttributes);
    }
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey[] keys) {
        this(editor, keys, null, null);
    }
    /** Creates a new instance. */
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey key, Icon icon) {
        this(editor, key, null, icon);
    }
    /** Creates a new instance. */
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey key, String name) {
        this(editor, key, name, null);
    }
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey key, String name, Icon icon) {
        this(editor, new AttributeKey[] {key}, name, icon);
    }
    public DefaultAttributeAction(DrawingEditor editor, AttributeKey[] keys, 
            String name, Icon icon) {
        this(editor, keys, name, icon, new HashMap<AttributeKey,Object>());
    }
    public DefaultAttributeAction(DrawingEditor editor, 
            AttributeKey[] keys, String name, Icon icon,
            Map<AttributeKey,Object> fixedAttributes) {
        super(editor);
        this.keys = keys;
        putValue(AbstractAction.NAME, name);
        putValue(AbstractAction.SMALL_ICON, icon);
        setEnabled(true);
        editor.addPropertyChangeListener(new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                if (evt.getPropertyName().equals(DefaultAttributeAction.this.keys[0])) {
                    putValue("attribute_"+DefaultAttributeAction.this.keys[0], evt.getNewValue());
                }
            }
            
        })
        ;
        this.fixedAttributes = fixedAttributes;
    }
    
    public void actionPerformed(java.awt.event.ActionEvent evt) {
        if (getView() != null && getView().getSelectionCount() > 0) {
            CompositeEdit edit = new CompositeEdit(labels.getString("drawAttributeChange"));
            fireUndoableEditHappened(edit);
            changeAttribute();
            fireUndoableEditHappened(edit);
        }
    }
    
    @SuppressWarnings("unchecked")
    public void changeAttribute() {
        CompositeEdit edit = new CompositeEdit("attributes");
        fireUndoableEditHappened(edit);
        Drawing drawing = getDrawing();
        Iterator i = getView().getSelectedFigures().iterator();
        while (i.hasNext()) {
            Figure figure = (Figure) i.next();
            figure.willChange();
            for (int j=0; j < keys.length; j++) {
                keys[j].basicSet(figure, getEditor().getDefaultAttribute(keys[j]));
            }
            for (Map.Entry<AttributeKey,Object> entry : fixedAttributes.entrySet()) {
                entry.getKey().basicSet(figure, entry.getValue());
                
            }
            figure.changed();
        }
        fireUndoableEditHappened(edit);
    }
    public void selectionChanged(FigureSelectionEvent evt) {
        //setEnabled(getView().getSelectionCount() > 0);
    }
}
