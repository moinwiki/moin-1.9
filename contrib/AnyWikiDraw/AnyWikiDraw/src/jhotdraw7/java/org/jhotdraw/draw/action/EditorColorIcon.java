/*
 * @(#)EditorColorIcon.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
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

import java.awt.*;
import java.net.*;
import org.jhotdraw.draw.*;
/**
 * EditorColorIcon draws a shape with the color of the specified default
 * attribute of the DrawingEditor onto the icon.
 * <p>
 * The behavior for choosing the drawn color matches with
 * {@link EditorColorChooserAction }.
 * 
 * @author Werner Randelshofer
 * @version $Id: EditorColorIcon.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class EditorColorIcon extends javax.swing.ImageIcon {
    private DrawingEditor editor;
    private AttributeKey<Color> key;
    private Shape colorShape;
    
    /** Creates a new instance. 
     * @param editor The drawing editor.
     * @param key The key of the default attribute
     * @param imageLocation the icon image
     * @param colorShape The shape to be drawn with the color of the default
     * attribute.
     */
    public EditorColorIcon(
            DrawingEditor editor,
            AttributeKey<Color> key, 
            URL imageLocation,
            Shape colorShape) {
        super(imageLocation);
        this.editor = editor;
        this.key = key;
        this.colorShape = colorShape;
    }
    public EditorColorIcon(
            DrawingEditor editor, 
            AttributeKey<Color> key, 
            Image image, 
            Shape colorShape) {
        super(image);
        this.editor = editor;
        this.key = key;
        this.colorShape = colorShape;
    }
    
    public void paintIcon(java.awt.Component c, java.awt.Graphics gr, int x, int y) {
        Graphics2D g = (Graphics2D) gr;
        super.paintIcon(c, g, x, y);
        Color color = (Color) editor.getDefaultAttribute(key);
        if (color != null) {
            g.setColor(color);
            g.translate(x, y);
            g.fill(colorShape);
            g.translate(-x, -y);
        }
    }    
}
