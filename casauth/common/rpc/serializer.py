import oslo_messaging as messaging
from osprofiler import profiler
from casauth.common.context import CasContext

from casauth.db import dto as md_dto


class CasSerializer(messaging.Serializer):
    def __init__(self, base=None):
        self._base = base

    def _serialize_entity(self, context, entity):
        return entity

    def serialize_entity(self, context, entity):
        if self._base:
            entity = self._base.serialize_entity(context, entity)

        return self._serialize_entity(context, entity)

    def _deserialize_entity(self, context, entity):
        return entity

    def deserialize_entity(self, context, entity):
        entity = self._deserialize_entity(context, entity)

        if self._base:
            entity = self._base.deserialize_entity(context, entity)

        return entity

    def _serialize_context(self, context):
        return context

    def serialize_context(self, context):
        if self._base:
            context = self._base.serialize_context(context)

        return self._serialize_context(context)

    def _deserialize_context(self, context):
        return context

    def deserialize_context(self, context):
        context = self._deserialize_context(context)

        if self._base:
            context = self._base.deserialize_context(context)

        # target_user = context.target_user
        # if target_user:
        #     context.target_user = md_dto.User.from_dict(target_user)
        #
        # request_user = context.request_user
        # if request_user:
        #     context.request_user = md_dto.User.from_dict(request_user)

        return context


class CasRequestContextSerializer(CasSerializer):
    def _serialize_context(self, context):
        _context = context.to_dict()
        prof = profiler.get()
        if prof:
            trace_info = {
                "hmac_key": prof.hmac_key,
                "base_id": prof.get_base_id(),
                "parent_id": prof.get_id()
            }
            _context.update({"trace_info": trace_info})
        return _context

    def _deserialize_context(self, context):
        trace_info = context.pop("trace_info", None)
        if trace_info:
            profiler.init(**trace_info)
        return CasContext.from_dict(context)
