/*
 * @(#)TextHolderFigure.java
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



package org.jhotdraw.draw;

import java.awt.*;
import org.jhotdraw.geom.*;

/**
 * The interface of a {@link Figure} that has some editable text contents.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Framework</em><br>
 * The text creation and editing tools and the {@code TextHolderFigure}
 * interface define together the contracts of a smaller framework inside of the
 * JHotDraw framework for  structured drawing editors.<br>
 * Contract: {@link TextHolderFigure}, {@link TextCreationTool},
 * {@link TextAreaCreationTool}, {@link TextEditingTool},
 * {@link TextAreaEditingTool}, {@link FloatingTextField},
 * {@link FloatingTextArea}.
 *
 * <p><em>Prototype</em><br>
 * The text creation tools create new figures by cloning a prototype
 * {@code TextHolderFigure} object.<br>
 * Prototype: {@link TextHolderFigure}; Client: {@link TextCreationTool},
 * {@link TextAreaCreationTool}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: TextHolderFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface TextHolderFigure extends Figure {
    // FIXME - Maybe we can remove method isEditable(), because we already have
    // an isInteractive() method in the Figure interface.
    /**
     * Returns true if the text of the TextHolderFigure can be edited.
     */
    public boolean isEditable();
    /**
     * Returns the font to be used by a text editor for editing this Figure.
     */
    public Font getFont();
    /**
     * Returns the text color to be used by a text editor for editing this Figure.
     */
    public Color getTextColor();
    /**
     * Returns the fill color to be used by a text editor for editing this Figure.
     */
    public Color getFillColor();
    
    // FIMXE - Maybe we can remove method getLabelFor().
    /**
     * Sometimes we want to use a TextHolderFigure as a label for another
     * TextHolderFigure. Returns the TextHolderFigure that should be really used.
     */
    public TextHolderFigure getLabelFor();
    /**
     * Gets the number of characters used to expand tabs.
     */
    public int getTabSize();
    
    // FIMXE - Maybe method getText and setText should work with StyledDocument
    //    instead of with Strings.
    /**
     * Returns the text held by the Text Holder.
     */
    public String getText();
    
    /**
     * Sets the text of the Text Holder.
     * @param text
     */
    public void setText(String text);
    /**
     * Gets the number of columns to be overlaid when the figure is edited.
     */
    public int getTextColumns();
    
    /**
     * Sets the font size of the text held by the TextHolderFigure.
     */
    public void setFontSize(float size);
    /**
     * Gets the font size of the text held by the TextHolderFigure.
     */
    public float getFontSize();
    /**
     * Gets the baseline of the first line of text, relative to the
     * upper left corner of the figure bounds.
     */
    public double getBaseline();
    
    /**
     * Returns Insets to be used by the text editor relative to the handle bounds
     * of the figure.
     */
    public Insets2D.Double getInsets();
    
    /**
     * Returns true, if the text does not fit into the bounds of the Figure.
     */
    public boolean isTextOverflow();
}
