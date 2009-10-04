/**
 * @(#)FontCollectionNode.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui.fontchooser;

import java.text.Collator;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Enumeration;
import javax.swing.tree.MutableTreeNode;
import javax.swing.tree.TreeNode;

/**
 * A FontCollectionNode is a MutableTreeNode which only allows FontFamilyNode
 * as child nodes.
 *
 * @author Werner Randelshofer
 * @version $Id: FontCollectionNode.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FontCollectionNode implements MutableTreeNode, Comparable<FontCollectionNode>, Cloneable {
    private MutableTreeNode parent;
    private String name;
    private ArrayList<FontFamilyNode> children;
    private boolean isEditable;

    public FontCollectionNode(String name) {
        this.name = name;
        children = new ArrayList<FontFamilyNode>();
    }

    public FontCollectionNode(String name, ArrayList<FontFamilyNode> families) {
        this.name = name;
        this.children = families;
    }

    public int compareTo(FontCollectionNode that) {
        return Collator.getInstance().compare(this.name, that.name);
    }
    
    public String getName() {
        return name;
    }
    
    @Override
    public String toString() {
        return name;
    }
    @Override
    public FontCollectionNode clone() {
        FontCollectionNode that;
        try {
            that = (FontCollectionNode) super.clone();
        } catch (CloneNotSupportedException ex) {
            InternalError error = new InternalError("Clone failed");
            error.initCause(ex);
            throw error;
        }
        that.parent = null;
        that.children = new ArrayList<FontFamilyNode>();
        for (FontFamilyNode f : this.children) {
            that.insert(f.clone(), that.getChildCount());
        }
        return that;
    }
    
    public void add(FontFamilyNode newChild) {
        insert(newChild, getChildCount());
    }
    public void addAll(Collection<FontFamilyNode> c) {
        children.addAll(c);
    }

    public void insert(MutableTreeNode newChild, int index) {
        FontCollectionNode oldParent = (FontCollectionNode) newChild.getParent();
        if (oldParent != null) {
            oldParent.remove(newChild);
        }
        newChild.setParent(this);
        children.add(index, (FontFamilyNode) newChild);
    }

    public void remove(int childIndex) {
	MutableTreeNode child = (MutableTreeNode)getChildAt(childIndex);
	children.remove(childIndex);
	child.setParent(null);
    }

    public void remove(MutableTreeNode aChild) {
	if (aChild == null) {
	    throw new IllegalArgumentException("argument is null");
	}

	if (!isNodeChild(aChild)) {
	    throw new IllegalArgumentException("argument is not a child");
	}
	remove(getIndex(aChild));	// linear search
    }

    public void setUserObject(Object object) {
        throw new UnsupportedOperationException("Not supported.");
    }

    public void removeFromParent() {
	if (parent != null) {
	    parent.remove(this);
	}
    }

    public void setParent(MutableTreeNode newParent) {
        this.parent = newParent;
    }

    public FontFamilyNode getChildAt(int childIndex) {
        return children.get(childIndex);
    }

    public int getChildCount() {
        return children.size();
    }

    public MutableTreeNode getParent() {
        return parent;
    }

    public int getIndex(TreeNode node) {
        return children.indexOf(node);
    }

    public boolean getAllowsChildren() {
        return true;
    }

    public boolean isLeaf() {
        return children.isEmpty();
    }

    public Enumeration children() {
        return Collections.enumeration(children);
    }
    
    public java.util.List<FontFamilyNode> families() {
        return Collections.unmodifiableList(children);
    }
    //
    //  Child Queries
    //

    /**
     * Returns true if <code>aNode</code> is a child of this node.  If
     * <code>aNode</code> is null, this method returns false.
     *
     * @return	true if <code>aNode</code> is a child of this node; false if 
     *  		<code>aNode</code> is null
     */
    public boolean isNodeChild(TreeNode aNode) {
	boolean retval;

	if (aNode == null) {
	    retval = false;
	} else {
	    if (getChildCount() == 0) {
		retval = false;
	    } else {
		retval = (aNode.getParent() == this);
	    }
	}

	return retval;
    }
    
    public boolean isEditable() {
        return isEditable;
    }
    public void setEditable(boolean newValue) {
        isEditable = newValue;
    }
}
