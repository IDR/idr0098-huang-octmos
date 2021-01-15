import argparse
import omero
import omero.cli
import omero.clients
from omero.gateway import BlitzGateway

project_id = 1403
dataset_id = 11960


def create_dataset(conn, project_id, dataset_name):
    dataset = omero.model.DatasetI()
    dataset.setName(omero.rtypes.rstring(dataset_name))
    dataset = conn.getUpdateService().saveAndReturnObject(dataset)
    dataset_id = dataset.getId().getValue()
    link = omero.model.ProjectDatasetLinkI()
    link.setParent(omero.model.ProjectI(project_id, False))
    link.setChild(omero.model.DatasetI(dataset.getId(), False))
    conn.getUpdateService().saveObject(link)
    return dataset_id


def unlink(conn, image):
    params = omero.sys.ParametersI()
    params.add('id', image.getId())
    query = "from DatasetImageLink as l where l.child.id=:id"
    query_service = conn.getQueryService()
    link = query_service.findAllByQuery(query, params,
                                                  conn.SERVICE_OPTS)
    links_ids = [link[0].getId().getValue()]
    conn.deleteObjects('DatasetImageLink', links_ids, wait=True)


def link_dataset(conn, dataset_id, image_id):
    link = omero.model.DatasetImageLinkI()
    link.setParent(omero.model.DatasetI(dataset_id, False))
    link.setChild(omero.model.ImageI(image_id, False))
    conn.getUpdateService().saveObject(link)

with omero.cli.cli_login() as c:
    conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
    cs = conn.getContainerService()
    param = omero.sys.ParametersI().leaves()
    project = cs.loadContainerHierarchy("Project", [project_id], param)[0]
    images = project.linkedDatasetList()[0].linkedImageList()

    overview_id = create_dataset(conn, project_id, "HE Overview")
    mask_id = create_dataset(conn, project_id, "HE Overview Mask")

    for image in images:
        if "macro image" in image.getName().getValue():
            unlink(conn, image)
            link_dataset(conn, overview_id, image.getId())
        if "macro mask image" in image.getName().getValue():
            unlink(conn, image)
            link_dataset(conn, mask_id, image.getId())

