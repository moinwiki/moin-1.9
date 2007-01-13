/*
 * @(#)FloatingTextField.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.*;
import java.awt.event.*;

/**
 * A text field overlay that is used to edit a TextFigure.
 * A FloatingTextField requires a two step initialization:
 * In a first step the overlay is created and in a
 * second step it can be positioned.
 *
 * @see TextFigure
 */
public  class FloatingTextField extends Object {

    private TextArea fEditWidget;

    private Container   fContainer;

    public FloatingTextField() {
        fEditWidget = new TextArea(5, 20);
    }

    /**
     * Creates the overlay for the given Component.
     */
    public void createOverlay(Container container) {
        createOverlay(container, null);
    }

    /**
     * Creates the overlay for the given Container using a
     * specific font.
     */
    public void createOverlay(Container container, Font font) {
        container.add(fEditWidget, 0);
        if (font != null)
            fEditWidget.setFont(font);
        fContainer = container;
	fEditWidget.requestFocus();
    }

    /**
     * Adds an action listener
     */
    public void addActionListener(ActionListener listener) {
	throw new RuntimeException("Adding action listener " + listener);
	//fEditWidget.addActionListener(listener);
    }

    /**
     * Remove an action listener
     */
    public void removeActionListener(ActionListener listener) {
	throw new RuntimeException("Removing action listener " + listener);
	// CC removed fEditWidget.removeActionListener(listener);
    }

    /**
     * Positions the overlay.
     */
    public void setBounds(Rectangle r, String text) {
	fEditWidget.setText(text);
        fEditWidget.setBounds(r.x, r.y, r.width, r.height);
        fEditWidget.setVisible(true);
	fEditWidget.selectAll();
	fEditWidget.requestFocus();
    }

    /**
     * Gets the text contents of the overlay.
     */
    public String getText() {
        return fEditWidget.getText();
    }

    /**
     * Gets the preferred size of the overlay.
     */
    public Dimension getPreferredSize(int rows, int cols) {
        return fEditWidget.getPreferredSize(rows, cols);
    }

    /**
     * Removes the overlay.
     */
    public void endOverlay() {
	fContainer.requestFocus();
	if (fEditWidget == null)
	    return;
	fEditWidget.setVisible(false);
	fContainer.remove(fEditWidget);

	Rectangle bounds = fEditWidget.getBounds();
	fContainer.repaint(bounds.x, bounds.y, bounds.width, bounds.height);
    }
}

