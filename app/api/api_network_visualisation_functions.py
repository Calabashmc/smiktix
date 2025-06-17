import os
from flask import request, jsonify
from flask_security import login_required
from sqlalchemy import select

from . import api_bp
from ..model import db
from ..model.model_cmdb import CmdbConfigurationItem


@api_bp.get('/network-data/')
@login_required
def get_network_data():
    id = request.args.get('id')
    depth = int(request.args.get('depth', 1))  # Default to depth 1 if not provided
    nodes = []
    edges = []
    visited_nodes = set()

    def fetch_related_nodes(ci, current_depth):
        if not ci or current_depth > depth or ci.id in visited_nodes:
            return
        if current_depth > depth:
            return
        visited_nodes.add(ci.id)

        # Add the current node
        nodes.append({
            'id': ci.id,
            'label': ci.name,
            'title': f'ID: {ci.id}<br>Name: {ci.name}<br>Status: {ci.status}',
            'shape': 'image',
            'image': f'/static/images/vis-network/{ci.icon}' if ci.icon else None,

        })

        # Fetch downstream and upstream nodes
        if hasattr(ci, 'downstream') and ci.downstream:
            for downstream_ci in ci.downstream:
                edges.append({
                    'from': ci.id,
                    'to': downstream_ci.id,
                    'arrows': 'to',
                    'title': f'From: {ci.name}<br>To: {downstream_ci.name}',
                })
                fetch_related_nodes(downstream_ci, current_depth + 1)

        if hasattr(ci, 'upstream') and ci.upstream:
            for upstream_ci in ci.upstream:
                edges.append({
                    'from': upstream_ci.id,
                    'to': ci.id,
                    'arrows': 'to',
                    'title': f'From: {upstream_ci.name}<br>To: {ci.name}',
                })
                fetch_related_nodes(upstream_ci, current_depth + 1)

        if hasattr(ci, 'components') and ci.components:
            for component_ci in ci.components:
                edges.append({
                    'from': ci.id,
                    'to': component_ci.id,
                    'arrows': 'to',
                    'title': f'From: {component_ci.name}<br>To: {ci.name}',  # Tooltip info
                })
                fetch_related_nodes(component_ci, current_depth + 1)

    # Start fetching from the provided CI or all nodes
    if id:
        cmdb_ci = db.session.execute(
            select(CmdbConfigurationItem).where(CmdbConfigurationItem.id == id)
        ).scalar_one_or_none()
        fetch_related_nodes(cmdb_ci, 1)
    else:
        # Fetch all nodes
        for item in db.session.execute(select(CmdbConfigurationItem)).scalars():
            fetch_related_nodes(item, 1)

    return jsonify({'nodes': nodes, 'edges': edges})


@api_bp.get('/get_cis_impacted/')
@login_required
def get_cis_impacted():
    ci_id = request.args.get('id')
    downstream_impacted = {}
    upstream_impacted = {}

    ci = db.session.execute(
        select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.id == ci_id)
    ).scalars().first()

    downstream_cis = ci.downstream.all()
    for downstream_ci in downstream_cis:
        downstream_impacted[downstream_ci.id] = downstream_ci.name

    upstream_cis = ci.upstream.all()
    for upstream_ci in upstream_cis:
        upstream_impacted[upstream_ci.id] = upstream_ci.name

    return jsonify({'upstream': upstream_impacted,
                    'downstream': downstream_impacted,
                    'name': ci.name,
                    'id': ci.id,
                    })


@api_bp.get('/get_vis_network_icon/')
@login_required
def get_vis_network_icon():
    ticket_number = request.args.get('ticket_number')

    ci = db.session.execute(
        select(CmdbConfigurationItem)
        .where(CmdbConfigurationItem.ticket_number == ticket_number)
    ).scalars().first()

    if ci:
        icon = ci.icon
    else:
        icon = 'alien.svg'

    return jsonify({'icon': icon})

