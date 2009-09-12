/*
 * @(#)DrawingColorChooserAction.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
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

import java.util.*;
import java.awt.*;
import javax.swing.*;
import org.jhotdraw.draw.*;
/**
 * The DrawingColorChooserAction changes a color attribute of the Drawing object
 * in the current view of the DrawingEditor.
 * <p>
 * The behavior for choosing the initial color of the JColorChooser matches with
 * {@link DrawingColorIcon }.
 * 
 * @author Werner Randelshofer
 * @version $Id: DrawingColorChooserAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DrawingColorChooserAction extends EditorColorChooserAction {
    
    /** Creates a new instance. */
    public DrawingColorChooserAction(DrawingEditor editor, AttributeKey<Color> key) {
        this(editor, key, null, null);
    }
    /** Creates a new instance. */
    public DrawingColorChooserAction(DrawingEditor editor, AttributeKey<Color> key, Icon icon) {
        this(editor, key, null, icon);
    }
    /** Creates a new instance. */
    public DrawingColorChooserAction(DrawingEditor editor, AttributeKey<Color> key, String name) {
        this(editor, key, name, null);
    }
    public DrawingColorChooserAction(DrawingEditor editor, final AttributeKey<Color> key, String name, Icon icon) {
        this(editor, key, name, icon, new HashMap<AttributeKey,Object>());
    }
    public DrawingColorChooserAction(DrawingEditor editor, final AttributeKey<Color> key, String name, Icon icon,
            Map<AttributeKey,Object> fixedAttributes) {
        super(editor, key, name, icon, fixedAttributes);
    }
    
    @Override
    public void actionPerformed(java.awt.event.ActionEvent e) {
        if (colorChooser == null) {
            colorChooser = new JColorChooser();
        }
        Color initialColor = getInitialColor();
        // FIXME - Reuse colorChooser object instead of calling static method here.
        Color chosenColor = colorChooser.showDialog((Component) e.getSource(), labels.getString("attribute.color.text"), initialColor);
        if (chosenColor != null) {
            HashMap<AttributeKey, Object> attr = new HashMap<AttributeKey, Object>(attributes);
            attr.put(key, chosenColor);
            HashSet<Figure> figures = new HashSet<Figure>();
            figures.add(getView().getDrawing());
            applyAttributesTo(attr, figures);
        }
    }

    @Override
    protected Color getInitialColor() {
        Color initialColor = null;
        
        DrawingView v = getEditor().getActiveView();
        if (v != null) {
            Figure f = v.getDrawing();
            initialColor = key.get(f);
        }
        if (initialColor == null) {
            initialColor = super.getInitialColor();
        }
        return initialColor;
    }
    protected void updateEnabledState() {
        if (getView() != null) {
            setEnabled(getView().isEnabled());
        } else {
            setEnabled(false);
        }
    }
    
}
