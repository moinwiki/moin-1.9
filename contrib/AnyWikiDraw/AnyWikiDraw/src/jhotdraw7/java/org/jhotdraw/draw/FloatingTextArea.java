/*
 *  @(#)FloatingTextArea.java
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

import java.awt.geom.*;
import java.awt.*;
import javax.swing.BorderFactory;
import javax.swing.JTextArea;
import javax.swing.JScrollPane;

/**
 * A <em>floating text area</em> that is used to edit a {@link TextHolderFigure}.
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
 * @author Werner Randelshofer
 * @version $Id: FloatingTextArea.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FloatingTextArea {

    /**
     * A scroll pane to allow for vertical scrolling while editing
     */
    protected JScrollPane editScrollContainer;
    /**
     * The actual editor
     */
    protected JTextArea textArea;
    /**
     * The drawing view.
     */
    protected DrawingView view;
    private TextHolderFigure editedFigure;
    private FigureListener figureHandler = new FigureAdapter() {

        @Override
        public void attributeChanged(FigureEvent e) {
            updateWidget();
        }
    };

    /**
     * Constructor for the FloatingTextArea object
     */
    public FloatingTextArea() {
        textArea = new JTextArea();
        textArea.setWrapStyleWord(true);
        textArea.setLineWrap(true);
        editScrollContainer = new JScrollPane(textArea,
                JScrollPane.VERTICAL_SCROLLBAR_ALWAYS,
                JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
        editScrollContainer.setCursor(Cursor.getPredefinedCursor(Cursor.DEFAULT_CURSOR));
        editScrollContainer.setBorder(BorderFactory.createLineBorder(Color.black));
    }

    /**
     * Creates the overlay within the given container.
     * @param view the DrawingView
     */
    public void createOverlay(DrawingView view) {
        createOverlay(view, null);
    }

    public void requestFocus() {
        textArea.requestFocus();
    }

    /**
     * Creates the overlay for the given Container using a
     * specific font.
     * @param view the DrawingView
     * @param figure the figure holding the text
     */
    public void createOverlay(DrawingView view, TextHolderFigure figure) {
        view.getComponent().add(editScrollContainer, 0);
        editedFigure = figure;
        this.view = view;
        if (editedFigure != null) {
            editedFigure.addFigureListener(figureHandler);
            updateWidget();
        }
    }

    protected void updateWidget() {
        Font f = editedFigure.getFont();
        // FIXME - Should scale with fractional value!
        f = f.deriveFont(f.getStyle(), (float) (editedFigure.getFontSize() * view.getScaleFactor()));
        textArea.setFont(f);
        textArea.setForeground(editedFigure.getTextColor());
        textArea.setBackground(editedFigure.getFillColor());
//        textArea.setBounds(getFieldBounds(editedFigure));
    }

    /**
     * Positions and sizes the overlay.
     * @param r the bounding Rectangle2D.Double for the overlay
     * @param text the text to edit
     */
    public void setBounds(Rectangle2D.Double r, String text) {
        textArea.setText(text);
        editScrollContainer.setBounds(view.drawingToView(r));
        editScrollContainer.setVisible(true);
        textArea.setCaretPosition(0);
        textArea.requestFocus();
    }

    /**
     * Gets the text contents of the overlay.
     * @return The text value
     */
    public String getText() {
        return textArea.getText();
    }

    /**
     * Gets the preferred size of the overlay.
     * @param cols Description of the Parameter
     * @return The preferredSize value
     */
    public Dimension getPreferredSize(int cols) {
        return new Dimension(textArea.getWidth(), textArea.getHeight());
    }

    /**
     * Removes the overlay.
     */
    public void endOverlay() {
        view.getComponent().requestFocus();
        if (editScrollContainer != null) {
            editScrollContainer.setVisible(false);
            view.getComponent().remove(editScrollContainer);

            Rectangle bounds = editScrollContainer.getBounds();
            view.getComponent().repaint(bounds.x, bounds.y, bounds.width, bounds.height);
        }
        if (editedFigure != null) {
            editedFigure.removeFigureListener(figureHandler);
            editedFigure = null;
        }
    }
}
