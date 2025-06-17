export default class OrgChart {
  constructor(options) {
    const defaultOptions = {
      nodeTitle: 'name',
      nodeId: 'id',
      toggleSiblingsResp: false,
      depth: 999,
      chartClass: '',
      exportButton: false,
      exportFilename: 'OrgChart',
      parentNodeSymbol: 'la-users',
      draggable: false,
      direction: 't2b',
      pan: false,
      zoom: false,
    };
    this.options = { ...defaultOptions, ...options };
    const data = this.options.data;
    const chart = document.createElement('div');
    const chartContainer = document.querySelector(this.options.chartContainer);

    if (!chartContainer) {
      throw new Error(`Chart container "${this.options.chartContainer}" not found.`);
    }

    this._name = 'OrgChart';
    this.chart = chart;
    this.chartContainer = chartContainer;
    chart.dataset.options = JSON.stringify(this.options);
    chart.setAttribute(
      'class',
      'orgchart' +
        (this.options.chartClass ? ' ' + this.options.chartClass : '') +
        (this.options.direction !== 't2b' ? ' ' + this.options.direction : '')
    );

    // Remove data from options for serialization
    delete this.options.data;

    // Load data and build chart
    if (typeof data === 'object') {
      this.buildHierarchy(chart, this.options.ajaxURL ? data : this._attachRel(data, '00'), 0);
    } else if (typeof data === 'string' && data.startsWith('#')) {
      const ul = document.querySelector(data)?.children[0];
      if (ul) {
        this.buildHierarchy(chart, this._buildJsonDS(ul), 0);
      }
    } else if (typeof data === 'string') {
      const spinner = document.createElement('i');
      spinner.setAttribute('class', 'la la-circle-o-notch la-spin spinner');
      chart.appendChild(spinner);
      this._getJSON(data)
        .then((resp) => {
          this.buildHierarchy(chart, this.options.ajaxURL ? resp : this._attachRel(resp, '00'), 0);
        })
        .catch((err) => {
          console.error('failed to fetch datasource for orgchart', err);
        })
        .finally(() => {
          const spinnerElem = chart.querySelector('.spinner');
          if (spinnerElem) spinnerElem.remove();
        });
    }

    chart.addEventListener('click', this._clickChart.bind(this));
    // Export Button
    if (this.options.exportButton && !chartContainer.querySelector('.oc-export-btn')) {
      const exportBtn = document.createElement('button');
      const downloadBtn = document.createElement('a');
      exportBtn.setAttribute('class', `oc-export-btn${this.options.chartClass ? ' ' + this.options.chartClass : ''}`);
      exportBtn.innerHTML = 'Export';
      exportBtn.addEventListener('click', this._clickExportButton.bind(this));
      downloadBtn.setAttribute('class', `oc-download-btn${this.options.chartClass ? ' ' + this.options.chartClass : ''}`);
      downloadBtn.setAttribute('download', `${this.options.exportFilename}.png`);
      chartContainer.appendChild(exportBtn);
      chartContainer.appendChild(downloadBtn);
    }
    // Pan & Zoom
    if (this.options.pan) {
      chartContainer.style.overflow = 'hidden';
      chart.addEventListener('mousedown', this._onPanStart.bind(this));
      chart.addEventListener('touchstart', this._onPanStart.bind(this));
      document.body.addEventListener('mouseup', this._onPanEnd.bind(this));
      document.body.addEventListener('touchend', this._onPanEnd.bind(this));
    }
    if (this.options.zoom) {
      chartContainer.addEventListener('wheel', this._onWheeling.bind(this));
      chartContainer.addEventListener('touchstart', this._onTouchStart.bind(this));
      document.body.addEventListener('touchmove', this._onTouchMove.bind(this));
      document.body.addEventListener('touchend', this._onTouchEnd.bind(this));
    }

    chartContainer.appendChild(chart);
  }

  get name() {
    return this._name;
  }

  // Utility functions (modern JS)
  _closest(el, fn) {
    return el && ((fn(el) && el !== this.chart) ? el : this._closest(el.parentElement, fn));
  }

  _siblings(el, expr) {
    return Array.from(el.parentElement?.children || []).filter((child) => {
      if (child !== el) {
        if (expr) return el.matches(expr);
        return true;
      }
      return false;
    });
  }

  _prevAll(el, expr) {
    const sibs = [];
    let prevSib = el.previousElementSibling;
    while (prevSib) {
      if (!expr || prevSib.matches(expr)) sibs.push(prevSib);
      prevSib = prevSib.previousElementSibling;
    }
    return sibs;
  }

  _nextAll(el, expr) {
    const sibs = [];
    let nextSib = el.nextElementSibling;
    while (nextSib) {
      if (!expr || nextSib.matches(expr)) sibs.push(nextSib);
      nextSib = nextSib.nextElementSibling;
    }
    return sibs;
  }

  _isVisible(el) {
    return el.offsetParent !== null;
  }

  _addClass(elements, classNames) {
    elements.forEach((el) => {
      classNames.split(' ').forEach((className) => el.classList.add(className));
    });
  }

  _removeClass(elements, classNames) {
    elements.forEach((el) => {
      classNames.split(' ').forEach((className) => el.classList.remove(className));
    });
  }

  _css(elements, prop, val) {
    elements.forEach((el) => {
      el.style[prop] = val;
    });
  }

  _removeAttr(elements, attr) {
    elements.forEach((el) => {
      el.removeAttribute(attr);
    });
  }

  _one(el, type, listener, self) {
    const one = function (event) {
      try {
        listener.call(self, event);
      } finally {
        el.removeEventListener(type, one);
      }
    };
    el.addEventListener(type, one);
  }

  _getDescElements(ancestors, selector) {
    let results = [];
    ancestors.forEach((el) => results.push(...el.querySelectorAll(selector)));
    return results;
  }

  async _getJSON(url) {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error(res.statusText);
    return res.json();
  }

  _buildJsonDS(li) {
    const subObj = {
      name: li.firstChild ? li.firstChild.textContent?.trim() : '',
      relationship:
        (li.parentElement?.parentElement?.nodeName === 'LI' ? '1' : '0') +
        (li.parentElement?.children.length > 1 ? 1 : 0) +
        (li.children.length ? 1 : 0)
    };
    if (li.id) subObj.id = li.id;
    const ul = li.querySelector('ul');
    if (ul) {
      subObj.children = [];
      Array.from(ul.children).forEach((el) => {
        subObj.children.push(this._buildJsonDS(el));
      });
    }
    return subObj;
  }

  _attachRel(data, flags) {
    data.relationship = flags + (data.children && data.children.length > 0 ? 1 : 0);
    if (data.children) {
      for (const item of data.children) {
        this._attachRel(item, '1' + (data.children.length > 1 ? 1 : 0));
      }
    }
    return data;
  }

  async _createNode(nodeData, level) {
    const opts = this.options;
    if (nodeData.children) {
      for (const child of nodeData.children) {
        child.parentId = nodeData.id;
      }
    }
    // Construct the content of node
    const nodeDiv = document.createElement('div');
    delete nodeData.children;
    nodeDiv.dataset.source = JSON.stringify(nodeData);
    if (nodeData[opts.nodeId]) nodeDiv.id = nodeData[opts.nodeId];
    const inEdit = this.chart.dataset.inEdit;
    const isHidden = inEdit
      ? inEdit === 'addChildren' ? ' slide-up' : ''
      : level >= opts.depth ? ' slide-up' : '';
    nodeDiv.setAttribute('class', `node ${nodeData.className || ''}${isHidden}`);
    if (opts.draggable) nodeDiv.setAttribute('draggable', 'true');
    if (nodeData.parentId) nodeDiv.setAttribute('data-parent', nodeData.parentId);

    nodeDiv.innerHTML = `
      <div class='title'>${nodeData[opts.nodeTitle]}</div>
      ${opts.nodeContent ? `<div class='content'>${nodeData[opts.nodeContent]}</div>` : ''}
    `;

    // Attach listeners as needed (add more for drag/drop, etc)
    nodeDiv.addEventListener('mouseenter', this._hoverNode?.bind(this));
    nodeDiv.addEventListener('mouseleave', this._hoverNode?.bind(this));
    nodeDiv.addEventListener('click', this._dispatchClickEvent?.bind(this));
    if (opts.draggable) {
      nodeDiv.addEventListener('dragstart', this._onDragStart?.bind(this));
      nodeDiv.addEventListener('dragover', this._onDragOver?.bind(this));
      nodeDiv.addEventListener('dragend', this._onDragEnd?.bind(this));
      nodeDiv.addEventListener('drop', this._onDrop?.bind(this));
    }
    if (opts.createNode) opts.createNode(nodeDiv, nodeData);

    return nodeDiv;
  }

  buildHierarchy(appendTo, nodeData, level, callback) {
    const opts = this.options;
    let nodeWrapper = null;
    const childNodes = nodeData.children;
    const isVerticalNode = opts.verticalDepth && (level + 1) >= opts.verticalDepth;

    if (!isVerticalNode) {
      nodeWrapper = document.createElement('table');
      appendTo.appendChild(nodeWrapper);
    } else {
      nodeWrapper = appendTo;
    }

    this._createNode(nodeData, level)
      .then((nodeDiv) => {
        if (isVerticalNode) {
          nodeWrapper.insertBefore(nodeDiv, nodeWrapper.firstChild);
        } else {
          // Draw the parent node
          const tr = document.createElement('tr');
          tr.innerHTML = `<td${childNodes ? ` colspan='${childNodes.length * 2}'` : ''}></td>`;
          tr.children[0].appendChild(nodeDiv);
          nodeWrapper.appendChild(tr);
        }

        // If there are children, draw lines and children rows
        if (childNodes && childNodes.length) {
          // Draw line from parent node down
          if (!isVerticalNode) {
            const downLineTr = document.createElement('tr');
            downLineTr.setAttribute('class', 'lines');
            downLineTr.innerHTML = `<td colspan='${childNodes.length * 2}'><div class='downLine'></div></td>`;
            nodeWrapper.appendChild(downLineTr);

            // Draw lines connecting to children
            const topLinesTr = document.createElement('tr');
            topLinesTr.setAttribute('class', 'lines');
            let tdHTML = "<td class='rightLine'>&nbsp;</td>";
            for (let i = 1; i < childNodes.length; i++) {
              tdHTML += "<td class='leftLine topLine'>&nbsp;</td><td class='rightLine topLine'>&nbsp;</td>";
            }
            tdHTML += "<td class='leftLine'>&nbsp;</td>";
            topLinesTr.innerHTML = tdHTML;
            nodeWrapper.appendChild(topLinesTr);
          }
          // Draw child nodes
          const nodeTr = isVerticalNode
            ? document.createElement('ul')
            : document.createElement('tr');
          if (!isVerticalNode) nodeTr.setAttribute('class', 'nodes');
          else nodeTr.setAttribute('class', 'verticalNodes');

          childNodes.forEach((child) => {
            let nodeCell;
            if (isVerticalNode) {
              nodeCell = document.createElement('li');
            } else {
              nodeCell = document.createElement('td');
              nodeCell.setAttribute('colspan', '2');
            }
            nodeTr.appendChild(nodeCell);
            this.buildHierarchy(nodeCell, child, level + 1, callback);
          });
          nodeWrapper.appendChild(nodeTr);
        }

        if (callback) callback();
      })
      .catch((err) => {
        console.error('Failed to create node', err);
      });
  }

  // Placeholder for hover/click logic, expand as needed
  _hoverNode(event) {}
  _dispatchClickEvent(event) {}
  _clickChart(event) {
    const closestNode = this._closest(event.target, (el) =>
      el.classList?.contains('node')
    );
    if (!closestNode && this.chart.querySelector('.node.focused')) {
      this.chart.querySelector('.node.focused')?.classList.remove('focused');
    }
  }
  _clickExportButton() {
    // Export logic (use html2canvas or similar)
    // Implement as needed, see original method
  }
  _onPanStart(event) {}
  _onPanEnd(event) {}
  _onWheeling(event) {}
  _onTouchStart(event) {}
  _onTouchMove(event) {}
  _onTouchEnd(event) {}

  // Exposed API
  getHierarchy() {
    if (!this.chart.querySelector('.node')?.id) {
      return 'Error: Nodes of orgchart to be exported must have id attribute!';
    }
    // Implement traversal logic as needed
    // return this._loopChart(this.chart.querySelector('table'));
    return {};
  }
}