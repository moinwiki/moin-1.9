/*
 * @(#)FigureEnumerator.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.framework.*;
import java.util.*;

/**
 * An Enumeration for a Vector of Figures.
 */
public final class FigureEnumerator implements FigureEnumeration {
    Vector v;
    Enumeration fEnumeration;

    public FigureEnumerator(Vector v) {
        this.v = v;
	    fEnumeration = v.elements();
    }

    /**
     * Returns true if the enumeration contains more elements; false
     * if its empty.
     */
    public boolean hasMoreElements() {
	    return fEnumeration.hasMoreElements();
    }

    /**
     * Returns the next element of the enumeration. Calls to this
     * method will enumerate successive elements.
     * @exception NoSuchElementException If no more elements exist.
     */
    public Object nextElement() {
        return fEnumeration.nextElement();
    }

    /**
     * Returns the next element of the enumeration. Calls to this
     * method will enumerate successive elements.
     * @exception NoSuchElementException If no more elements exist.
     */
    public Figure nextFigure() {
        return (Figure)fEnumeration.nextElement();
    }

    /**
     * Returns true if thje enumeration contains the specified figure
     * @param   figure      the figure to check
     */
    public boolean contains(Figure figure) {
        return v.contains(figure);
    }
}
