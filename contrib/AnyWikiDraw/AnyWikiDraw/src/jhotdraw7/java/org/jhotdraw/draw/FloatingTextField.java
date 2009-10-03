/*
 * @(#)FloatingTextField.java
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

package org.jhotdraw.draw;

import javax.swing.*;
import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * A <em>floating text field</em> that is used to edit a {@link TextHolderFigure}.
 * <p>
 * {@code FloatingTextField} requires a two step initialization:
 * In a first step the overlay is created and in a
 * second step it can be positioned.
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
 * <hr>
 *
 * @see org.jhotdraw.draw.TextFigure
 *
 * @author Werner Randelshofer
 * @version $Id: FloatingTextField.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public  class FloatingTextField {
    private TextHolderFigure editedFigure;
    private JTextField   textField;
    private DrawingView   view;
    private FigureListener figureHandler = new FigureAdapter() {
        @Override
        public void attributeChanged(FigureEvent e) {
            updateWidget();
        }
    };
    
    public FloatingTextField() {
        textField = new JTextField(20);
    }
    
    /**
     * Creates the overlay for the given Component.
     */
    public void createOverlay(DrawingView view) {
        createOverlay(view, null);
    }
    
    public void requestFocus() {
        textField.requestFocus();
    }
    
    /**
     * Creates the overlay for the given Container using a
     * specific font.
     */
    public void createOverlay(DrawingView view, TextHolderFigure figure) {
        view.getComponent().add(textField, 0);
        textField.setText(figure.getText());
        textField.setColumns(figure.getTextColumns());
        textField.selectAll();
        textField.setVisible(true);
        editedFigure = figure;
        editedFigure.addFigureListener(figureHandler);
        this.view = view;
        updateWidget();
    }
    
    protected void updateWidget() {
        Font font = editedFigure.getFont();
        font = font.deriveFont(font.getStyle(), (float) (editedFigure.getFontSize() * view.getScaleFactor()));
        textField.setFont(font);
        textField.setForeground(editedFigure.getTextColor());
        textField.setBackground(editedFigure.getFillColor());

        Rectangle2D.Double fDrawBounds = editedFigure.getBounds();
        Point2D.Double fDrawLoc = new Point2D.Double(fDrawBounds.getX(), fDrawBounds.getY());
        if (TRANSFORM.get(editedFigure) != null) {
        TRANSFORM.get(editedFigure).transform(fDrawLoc, fDrawLoc);
        }
        Point fViewLoc = view.drawingToView(fDrawLoc);
        Rectangle fViewBounds = view.drawingToView(fDrawBounds);
        fViewBounds.x = fViewLoc.x;
        fViewBounds.y = fViewLoc.y;
        Dimension tfDim = textField.getPreferredSize();
        Insets tfInsets = textField.getInsets();
        float fontBaseline = textField.getGraphics().getFontMetrics(font).getMaxAscent();
        double fBaseline = editedFigure.getBaseline() * view.getScaleFactor();
        textField.setBounds(
                fViewBounds.x - tfInsets.left,
                fViewBounds.y - tfInsets.top - (int) (fontBaseline - fBaseline),
                Math.max(fViewBounds.width + tfInsets.left + tfInsets.right, tfDim.width),
                Math.max(fViewBounds.height + tfInsets.top + tfInsets.bottom, tfDim.height)
                );
    }
    
    public Insets getInsets() {
        return textField.getInsets();
    }
    
    /**
     * Adds an action listener
     */
    public void addActionListener(ActionListener listener) {
        textField.addActionListener(listener);
    }
    
    /**
     * Remove an action listener
     */
    public void removeActionListener(ActionListener listener) {
        textField.removeActionListener(listener);
    }
    
    
    /**
     * Gets the text contents of the overlay.
     */
    public String getText() {
        return textField.getText();
    }
    
    /**
     * Gets the preferred size of the overlay.
     */
    public Dimension getPreferredSize(int cols) {
        textField.setColumns(cols);
        return textField.getPreferredSize();
    }
    
    /**
     * Removes the overlay.
     */
    public void endOverlay() {
        view.getComponent().requestFocus();
        if (textField != null) {
            textField.setVisible(false);
            view.getComponent().remove(textField);
            
            Rectangle bounds = textField.getBounds();
            view.getComponent().repaint(bounds.x, bounds.y, bounds.width, bounds.height);
        }
        if (editedFigure != null) {
            editedFigure.removeFigureListener(figureHandler);
            editedFigure = null;
        }
    }
}

