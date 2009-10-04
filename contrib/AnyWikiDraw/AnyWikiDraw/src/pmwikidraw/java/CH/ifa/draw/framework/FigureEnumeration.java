/*
 * @(#)FigureEnumeration.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.util.*;

/**
 * Interface for Enumerations that access Figures.
 * It provides a method nextFigure, that hides the down casting
 * from client code.
 */
public interface FigureEnumeration extends Enumeration {
    /**
     * Returns the next element of the enumeration. Calls to this
     * method will enumerate successive elements.
     * @exception NoSuchElementException If no more elements exist.
     */
    public Figure nextFigure();

    /**
     * Returns true if thje enumeration contains the specified figure
     * @param   figure      the figure to check
     */
    public boolean contains(Figure figure);
}
