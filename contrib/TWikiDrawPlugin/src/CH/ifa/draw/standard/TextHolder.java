/*
 * @(#)TextHolder.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.util.*;
import CH.ifa.draw.framework.*;

/**
 * The interface of a figure that has some editable text contents.
 * @see Figure
 */

public interface TextHolder {

    public Rectangle textDisplayBox();

    /**
     * Gets the text shown by the text figure.
     */
    public String getText();

    /**
     * Sets the text shown by the text figure.
     */
    public void setText(String newText);

    /**
     * Tests whether the figure accepts typing.
     */
    public boolean acceptsTyping();

    /**
     * Gets the number of columns to be overlaid when the figure is edited.
     */
    public int overlayColumns();

    /**
     * Gets the number of rows to be overlaid when the figure is edited.
     */
    public int overlayRows();

    /**
     * Connects a figure to another figure.
     */
    public void connect(Figure connectedFigure);

    /**
     * Gets the font.
     */
    public Font getFont();

}
