/*
 * @(#)AbstractLocator.java
 *
 * Project:		JHotdraw - a GUI framework for technical drawings
 *				http://www.jhotdraw.org
 *				http://jhotdraw.sourceforge.net
 * Copyright:	© by the original author(s) and all contributors
 * License:		Lesser GNU Public License (LGPL)
 *				http://www.opensource.org/licenses/lgpl-license.html
 */

package org.jhotdraw.standard;

import org.jhotdraw.util.*;
import org.jhotdraw.framework.*;

import java.io.IOException;


/**
 * AbstractLocator provides default implementations for
 * the Locator interface.
 *
 * @see Locator
 * @see Handle
 *
 * @version <$CURRENT_VERSION$>
 */
public abstract class AbstractLocator implements Locator, Storable, Cloneable {

	/*
	 * Serialization support.
	 */
	private static final long serialVersionUID = -7742023180844048409L;

	protected AbstractLocator() {
	}

	public Object clone() {
		try {
			return super.clone();
		}
		catch (CloneNotSupportedException e) {
			throw new InternalError();
		}
	}

	/**
	 * Stores the arrow tip to a StorableOutput.
	 */
	public void write(StorableOutput dw) {
	}
    
	/* Added by CJ 13/11/04 */
	public String getMap() {
    	return "";
    }
	
	/**
	 * Reads the arrow tip from a StorableInput.
	 */
	public void read(StorableInput dr) throws IOException {
	}
}


