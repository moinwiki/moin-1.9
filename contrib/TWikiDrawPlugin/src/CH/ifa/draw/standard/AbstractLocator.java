/*
 * @(#)AbstractLocator.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

import java.awt.*;
import java.util.*;
import java.io.*;

/**
 * AbstractLocator provides default implementations for
 * the Locator interface.
 *
 * @see Locator
 * @see Handle
 */

public abstract class AbstractLocator
                implements Locator, Storable, Cloneable {

    protected AbstractLocator() {
    }

    public Object clone() {
        try {
            return super.clone();
        } catch (CloneNotSupportedException e) {
	        throw new InternalError();
        }
    }

    /**
     * Stores the arrow tip to a StorableOutput.
     */
    public void write(StorableOutput dw) {
    }

    public String getMap() {
	return "";
    }

    /**
     * Reads the arrow tip from a StorableInput.
     */
    public void read(StorableInput dr) throws IOException {
    }
}


