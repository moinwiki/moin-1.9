/*
 * Created on 30-Dec-2004
 *
 */
package com.wombatinvasion.pmwikidraw.symbol;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.List;
import java.util.Stack;

import qdxml.DocHandler;

/**
 * @author Ciaran Jessup
 */
public class SymbolPackage implements DocHandler {

	private String author = "";
	private String creationDate = "";
	
	private MultiLanguageString name = new MultiLanguageString(); 
	private MultiLanguageString description = new MultiLanguageString(); 
	
	Stack stack = null;
	
	private List symbolGroups = new ArrayList();
	SymbolGroup defaultGroup = new SymbolGroup(); // For symbols not belonging to a group.
	
	private class XmlNode {
		public XmlNode(String tag, Hashtable attributes) {
			this.tag = tag;
			this.attr = attributes;
		}
		String tag;
		Hashtable attr;
	}
	public class Symbol {
		public String location;
		public MultiLanguageString name = new MultiLanguageString();
	}
	public class SymbolGroup {
		public MultiLanguageString name = new MultiLanguageString();
		public MultiLanguageString description= new MultiLanguageString();
		public List symbols = new ArrayList();
	}
	
	private class SymbolPackageDefinition {
		HashSet names = new HashSet();
		HashSet descriptions = new HashSet();
		String author;
		String creationDate;
		
		public String toString() {
			StringBuffer result = new StringBuffer();
			Iterator namesIt = names.iterator();
			while(namesIt.hasNext()) {
				result.append((String)namesIt.next()+", ");
			}
			return result.toString();
		}
	}
	
	/**
	 * 
	 */
	public SymbolPackage() {
		super();
		symbolGroups.clear();
	}
	
	SymbolGroup activeSymbolGroup = null;
	
	Symbol currentSymbol = null;
	
	/* (non-Javadoc)
	 * @see qdxml.DocHandler#startElement(java.lang.String, java.util.Hashtable)
	 */
	public void startElement(String tag, Hashtable h) throws Exception {
		
		Iterator attributes = h.keySet().iterator();

		String lCaseTag = tag.toLowerCase();
		if(stack.size()>0) {
			if(lCaseTag.equals("symbol-group"))  
			{
				activeSymbolGroup = new SymbolGroup();
				while(attributes.hasNext()) {
					String attributeName = (String)attributes.next();
					String attributeValue = (String)h.get(attributeName);
					if(attributeName.equals("name")) {
						activeSymbolGroup.name.addString(null, attributeValue);
					}
				}
				symbolGroups.add(activeSymbolGroup);
			}
			else if(lCaseTag.equals("symbol")) 
			{
				Symbol symbol = new Symbol();
				currentSymbol = symbol;
				while(attributes.hasNext()) {
					String attributeName = (String)attributes.next();
					String attributeValue = (String)h.get(attributeName);
					if(attributeName.equals("location")) {
						symbol.location = attributeValue;
					}
					else if(attributeName.equals("name")) {
						symbol.name.addString( null, attributeValue );
					}
				}
				
				if(activeSymbolGroup != null) {
					activeSymbolGroup.symbols.add(symbol);
				} else {
					defaultGroup.symbols.add(symbol);
				}
				
			}
		} 
		else {
			//Top level element...
			while(attributes.hasNext()) {
				String attributeName = (String)attributes.next();
				String attributeValue = (String)h.get(attributeName);
				if(attributeName.toLowerCase().equals("author")) {
					this.author = attributeValue;
				}
				else if(attributeName.toLowerCase().equals("creation-date")) {
					this.creationDate = attributeValue;
				}
				else if(attributeName.toLowerCase().equals("name")) {
					this.name.addString(null, attributeValue); // Assign default language
				}
			}
		}
		
		stack.push(new XmlNode(lCaseTag, h));
	}

	/* (non-Javadoc)
	 * @see qdxml.DocHandler#endElement(java.lang.String)
	 */
	public void endElement(String tag) throws Exception {
		stack.pop();
		String lCaseTag = tag.toLowerCase(); 
		if(lCaseTag.equals("symbol-group")) {
			activeSymbolGroup = null;
		}
		else if(lCaseTag.equals("symbol-group")) {
			currentSymbol = null;
		}
	}

	/* (non-Javadoc)
	 * @see qdxml.DocHandler#startDocument()
	 */
	public void startDocument() throws Exception {
		stack = new Stack();
	}

	/* (non-Javadoc)
	 * @see qdxml.DocHandler#endDocument()
	 */
	public void endDocument() throws Exception {
		stack = null;
		if(defaultGroup.symbols.size()>0) {
			// Only add the default group iff it contains some elements.
			defaultGroup.name.addString(null, "Default");
			symbolGroups.add(0, defaultGroup);
		}

	}

	/* (non-Javadoc)
	 * @see qdxml.DocHandler#text(java.lang.String)
	 */
	public void text(String str) throws Exception {
		if(stack.size()>0) {
			XmlNode parent = (XmlNode)stack.peek();
			if(parent.tag.equals("package-name")) {
				name.addString((String)parent.attr.get("lang"), str);
			}
			else if(parent.tag.equals("package-description")) {
				description.addString((String)parent.attr.get("lang"), str);
			}
			else if(parent.tag.equals("symbol-group-name")) {
				if(activeSymbolGroup!=null) {
					activeSymbolGroup.name.addString((String)parent.attr.get("lang"), str);
				} 
				else {
					System.err.println("Error processing manifest document, 'symbol-group-name' in invalid place.");
				}
			}
			else if(parent.tag.equals("symbol-group-description")) {
				if(activeSymbolGroup!=null) {
					activeSymbolGroup.description.addString((String)parent.attr.get("lang"), str);
				} 
				else {
					System.err.println("Error processing manifest document, 'symbol-group-description' in invalid place.");
				}
			}
			else if(parent.tag.equals("symbol-name")) {
				if(currentSymbol!=null) {
					currentSymbol.name.addString((String)parent.attr.get("lang"), str);
				} 
				else {
					System.err.println("Error processing manifest document, 'symbol-name' in invalid place.");
				}
			}
		}
	}
	

	
	public String toString() {
		StringBuffer result = new StringBuffer();
		result.append("Package Name:"+name+"\nCreated by:"+author+"\nCreated at:"+creationDate);
		for(int i=0;i<symbolGroups.size();i++){
			
			SymbolGroup symbolGroup = (SymbolGroup)symbolGroups.get(i);
			result.append("\n"+symbolGroup.name+"; "+ symbolGroup.description+" ->");
			for(int j=0;j<symbolGroup.symbols.size();j++) {
				Symbol symbol = (Symbol) symbolGroup.symbols.get(j);
				result.append("\n\t"+symbol.name+"; "+ symbol.location);
			}
		}
		return result.toString(); 
	}
	
	
	public String getName() {
		return name.getLocaleString();
	}

	public int getSymbolGroupCount() {
		return symbolGroups.size();
	}
	
	public List getSymbolGroups() {
		return symbolGroups;
	}
}
