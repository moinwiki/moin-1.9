/*
 * @(#)DOMStorable.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.xml;

import java.io.*;
/**
 * Interface for objects that can be made persistent using 
 * <code>DOMOutput.writeObject</code> and <code>DOMInput.readObject</code>.
 * <p>
 * By convention every object implementing the DOMStorable interface MUST
 * provide a public parameterless constructor.
 *
 * @author  Werner Randelshofer
 * @version $Id: DOMStorable.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface DOMStorable {
    public void write(DOMOutput out) throws IOException;
    public void read(DOMInput in) throws IOException;
}
